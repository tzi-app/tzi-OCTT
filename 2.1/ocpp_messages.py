"""OCPP-J 2.1 message helpers, shared by the mock Charging Station (charge_point.py) and the
CSMS simulator (csms.py).

Field names. Python code in this suite writes OCPP fields in snake_case, as the OCPP 2.0.1
suite does. On the wire they are the names of the OCPP 2.1 JSON schemas:

- `to_ocpp()` turns snake_case data into a message payload. It walks the schema of the
  message next to the data and takes every field name from the schema. The generic conversion
  of the ocpp library is not exact for OCPP 2.1: 43 field names do not survive it, for example
  `setpoint_L2`, `fixedPFAbsorb`, `receiptUrl`, `taxRuleID`, `soC` and `evSupportedDERControl`.
- `from_ocpp()` turns a received payload into snake_case `Payload` objects. These names are the
  ones the ocpp library produces: `setpoint_L2` is `setpoint_l2`, `fixedPFAbsorb` is
  `fixed_pf_absorb`, `iso15118CertificateHashData` is `iso15118_certificate_hash_data`, and
  `v2xChargingParameters` is `v2x_charging_parameters`.

Schemas. Messages are checked against the OCPP 2.1 JSON schemas that ship with the ocpp
library (`ocpp/v21/schemas`). They are identical to the official Part 3 schemas.
"""

import dataclasses
import enum
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

import jsonschema
import ocpp.v21
from ocpp.charge_point import camel_to_snake_case

# OCPP-J 2.1, 4.1.3 "The message type"
CALL = 2
CALL_RESULT = 3
CALL_ERROR = 4
CALL_RESULT_ERROR = 5
SEND = 6

MESSAGE_TYPE_NAMES = {
    CALL: 'CALL',
    CALL_RESULT: 'CALL_RESULT',
    CALL_ERROR: 'CALL_ERROR',
    CALL_RESULT_ERROR: 'CALL_RESULT_ERROR',
    SEND: 'SEND',
}

SUBPROTOCOL = 'ocpp2.1'

SCHEMA_DIR = Path(ocpp.v21.__file__).resolve().parent / 'schemas'

# The actions of OCPP 2.1: every message that has a <Action>Request schema.
ACTIONS = frozenset(
    path.name[:-len('Request.json')] for path in SCHEMA_DIR.glob('*Request.json')
)

# Messages that are sent with the SEND message type: no response, no Request suffix.
UNCONFIRMED_ACTIONS = frozenset({'NotifyPeriodicEventStream'})


def utc_now_iso(offset_seconds=0):
    """The current time (plus an offset) as an OCPP dateTime: RFC 3339, in UTC."""
    moment = datetime.now(timezone.utc)
    if offset_seconds:
        from datetime import timedelta
        moment += timedelta(seconds=offset_seconds)
    return moment.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


# ─── Field names ─────────────────────────────────────────────────────────────

@lru_cache(maxsize=None)
def snake_name(name):
    """The snake_case name of an OCPP field, as the ocpp library produces it."""
    return next(iter(camel_to_snake_case({name: None})))


def canonical(name):
    """A spelling-independent key: iso15118SchemaVersion, iso_15118_schema_version and
    iso15118_schema_version are the same field."""
    return name.replace('_', '').lower()


_canonical = canonical


def _generic_camel(name):
    """camelCase for a name the schema does not know."""
    if '_' not in name:
        return name
    head, *rest = name.split('_')
    return head + ''.join(part[:1].upper() + part[1:] for part in rest)


# ─── Schemas ─────────────────────────────────────────────────────────────────

@lru_cache(maxsize=None)
def load_schema(schema_name):
    """A schema by its name without `.json`: `ResetRequest`, `ResetResponse`,
    `NotifyPeriodicEventStream`."""
    path = SCHEMA_DIR / f'{schema_name}.json'
    with open(path, encoding='utf-8-sig') as schema_file:
        return json.load(schema_file)


def has_schema(schema_name):
    return (SCHEMA_DIR / f'{schema_name}.json').exists()


def _resolve(node, root):
    while isinstance(node, dict) and '$ref' in node:
        node = root['definitions'][node['$ref'].rsplit('/', 1)[1]]
    return node


_DATE_TIME = re.compile(
    r'^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d{1,3})?([Zz]|[+-]\d{2}:\d{2})$'
)
_format_checker = jsonschema.FormatChecker(formats=())


@_format_checker.checks('date-time')
def _is_ocpp_date_time(value):
    """OCPP dateTime (Part 2, 2.1.4 "Primitive Datatypes"): formatted as defined in RFC 3339,
    with at most 3 decimal places for the fractional seconds. jsonschema only checks this
    format with an extra package, and does not know the limit on the decimal places.
    """
    if not isinstance(value, str):
        return True
    if not _DATE_TIME.match(value):
        return False
    try:
        datetime.fromisoformat(value.upper().replace('Z', '+00:00'))
    except ValueError:
        return False
    return True


@lru_cache(maxsize=None)
def _validator(schema_name):
    return jsonschema.Draft6Validator(load_schema(schema_name), format_checker=_format_checker)


# The RPC framework error code (OCPP-J 2.1, 4.3) that fits a schema violation.
_ERROR_CODE_BY_KEYWORD = {
    'type': 'TypeConstraintViolation',
    'required': 'OccurrenceConstraintViolation',
    'minItems': 'OccurrenceConstraintViolation',
    'maxItems': 'OccurrenceConstraintViolation',
    'enum': 'PropertyConstraintViolation',
    'maxLength': 'PropertyConstraintViolation',
    'minimum': 'PropertyConstraintViolation',
    'maximum': 'PropertyConstraintViolation',
    'format': 'PropertyConstraintViolation',
    'additionalProperties': 'FormatViolation',
}


class SchemaViolation(Exception):
    """A payload does not match its OCPP 2.1 JSON schema."""

    def __init__(self, schema_name, problems, error_code, payload):
        self.schema_name = schema_name
        self.problems = problems
        self.error_code = error_code
        self.payload = payload
        super().__init__(
            f"{schema_name} does not match the OCPP 2.1 schema: " + '; '.join(problems)
            + f" | payload: {json.dumps(payload, default=str)}"
        )


def validate(schema_name, payload):
    """Check a camelCase payload against its schema. Raises SchemaViolation."""
    errors = sorted(_validator(schema_name).iter_errors(payload), key=lambda e: list(e.path))
    if not errors:
        return
    problems = []
    for error in errors:
        where = '.'.join(str(part) for part in error.path) or '(payload)'
        problems.append(f"{where}: {error.message}")
    error_code = _ERROR_CODE_BY_KEYWORD.get(errors[0].validator, 'FormatViolation')
    raise SchemaViolation(schema_name, problems, error_code, payload)


# ─── Python data -> payload ──────────────────────────────────────────────────

def to_ocpp(schema_name, data):
    """A message payload (camelCase, as on the wire) from snake_case data.

    `data` is a dataclass of the ocpp library (`ocpp.v21.call`, `call_result`, `datatypes`), a
    dict, or a mix of them. Fields that are None are left out: OCPP has no null fields
    (OCPP-J 2.1, 4.1.5). Field names come from the schema, whatever their spelling in Python,
    and a name the schema does not know is sent as it is (in camelCase), so that a test can
    send a message that is not valid on purpose.
    """
    schema = load_schema(schema_name)
    return _to_ocpp(data, schema, schema)


def _to_ocpp(value, node, root):
    node = _resolve(node, root) if node is not None else None

    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        value = {field.name: getattr(value, field.name) for field in dataclasses.fields(value)}

    if isinstance(value, dict):
        properties = (node or {}).get('properties', {})
        by_canonical = {_canonical(name): name for name in properties}
        # CustomDataType is the one open object: its extra fields are vendor data.
        open_object = node is not None and node.get('additionalProperties') is not False
        payload = {}
        for key, item in value.items():
            if item is None:
                continue
            name = by_canonical.get(_canonical(key))
            if name is not None:
                payload[name] = _to_ocpp(item, properties[name], root)
            elif open_object and node.get('properties'):
                payload[key] = _to_ocpp(item, None, root)
            else:
                payload[_generic_camel(key)] = _to_ocpp(item, None, root)
        return payload

    if isinstance(value, (list, tuple)):
        items = (node or {}).get('items')
        return [_to_ocpp(item, items, root) for item in value if item is not None]

    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    return value


# ─── Payload -> Python data ──────────────────────────────────────────────────

class Payload(dict):
    """A received OCPP object with snake_case keys.

    Fields are read as attributes or as keys: `request.evse_id`, `request['evse_id']`. A field
    of the schema that the sender left out reads as None, so "must be omitted" is
    `request.evse_id is None`. A name that is not a field of the object raises, so that a typo
    in a test cannot pass as an omitted field. Underscores do not matter in a name:
    `iso15118_schema_version` and `iso_15118_schema_version` are the same field.

    `in`, `get()`, iteration and comparison work as for the dict of the fields that were sent.
    An attribute that is a field of the object is that field, also when dict has a method of
    that name (`request.clear`); `dict.values(payload)` still gives the method.
    """

    __slots__ = ('_fields', '_type')

    def __init__(self, data, fields=None, type_name=None):
        super().__init__(data)
        self._fields = fields
        self._type = type_name or 'object'

    def __missing__(self, key):
        if self._fields is None or key in self._fields:
            return None
        # Another spelling of a field: prioritized_emaids for prioritizedEMAIDs, which the
        # conversion to snake_case turns into prioritized_emai_ds.
        wanted = canonical(key)
        for field in self._fields:
            if canonical(field) == wanted:
                return dict.get(self, field)
        raise KeyError(
            f"{key!r} is not a field of {self._type}. Its fields: {', '.join(sorted(self._fields))}"
        )

    def __getattribute__(self, name):
        # A field of the object comes before a method of dict with the same name: `clear` of
        # CustomerInformationRequest, `values` of PeriodicEventStreamParamsType.
        if not name.startswith('_'):
            try:
                fields = object.__getattribute__(self, '_fields')
            except AttributeError:
                fields = None
            if name in fields if fields is not None else dict.__contains__(self, name):
                return self[name]
        return object.__getattribute__(self, name)

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(error.args[0]) from None


def from_ocpp(schema_name, payload):
    """Snake_case `Payload` objects from a received payload (camelCase)."""
    schema = load_schema(schema_name) if schema_name and has_schema(schema_name) else None
    return _from_ocpp(payload, schema, schema, schema_name)


def _from_ocpp(value, node, root, type_name):
    if node is not None:
        if '$ref' in node:
            type_name = node['$ref'].rsplit('/', 1)[1]
        node = _resolve(node, root)

    if isinstance(value, dict):
        properties = (node or {}).get('properties')
        open_object = node is None or node.get('additionalProperties') is not False
        # The extra fields of the one open object, CustomDataType, are vendor data: they keep
        # their names.
        vendor_data = node is not None and open_object
        data = {}
        for key, item in value.items():
            child = properties.get(key) if properties else None
            if vendor_data and child is None:
                data[key] = item
            else:
                data[snake_name(key)] = _from_ocpp(item, child, root, key)
        fields = None
        if properties is not None and not open_object:
            fields = frozenset(snake_name(name) for name in properties)
        return Payload(data, fields, type_name)

    if isinstance(value, list):
        items = (node or {}).get('items')
        return [_from_ocpp(item, items, root, type_name) for item in value]

    return value
