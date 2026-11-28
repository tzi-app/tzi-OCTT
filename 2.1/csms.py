"""
CSMS (Charging Station Management System) simulator for the OCPP 2.1 test suite.

Note: This implementation is intended solely for testing, debugging, and stepping through
      the tzi-octt test suite. It is NOT designed to be used in production.
      It was written by Anthropic Claude.

It is a minimal in-memory CSMS: just enough behavior, per the OCPP 2.1 specification, for the
2.1 tests to be checked against. Nothing is stored, so a restart resets it.

Runs three servers. All settings, ports included, come from config.json next to this file; no
environment variables are read.
  - WSS on CSMS_WSS_PORT (9000): TLS, with Basic Auth (security profiles 1 and 2) or a client
    certificate (security profile 3). The tests connect here (CSMS_ADDRESS in pytest.ini).
  - Trigger API (HTTP) on CSMS_TRIGGER_PORT (5001): the endpoints the tests call to make the
    CSMS send a request (CSMS_TRIGGER_ADDRESS in pytest.ini). It is also the log server of the
    CSMS over HTTP (TC_N_102).
  - The log server of the CSMS over HTTPS on CSMS_LOG_HTTPS_PORT (5002), for TC_N_103.

Usage (OCPP 2.1 only):
  python 2.1/csms.py                    # from the repository root; works from any directory

  The simulator is ready when it logs "CSMS 2.1 simulator started."; then run the 2.1 tests
  as usual.

Stations:
  STATIONS in config.json maps each station ID to its security profile. A station ID that is
  not in it is refused (HTTP 404).

Every message is checked against its OCPP 2.1 JSON schema: a request of a station that does
not match is answered with a CALLERROR.
"""

import asyncio
import base64
import http
import json
import logging
import secrets
import ssl
import string
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import websockets
from websockets.exceptions import ConnectionClosed
from websockets.legacy.server import WebSocketServerProtocol

# Keep local imports stable after project restructuring.
_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parent
for _path in (str(_MODULE_DIR), str(_PROJECT_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from ocpp_messages import (
    ACTIONS,
    CALL,
    CALL_ERROR,
    CALL_RESULT,
    CALL_RESULT_ERROR,
    SEND,
    SUBPROTOCOL,
    UNCONFIRMED_ACTIONS,
    SchemaViolation,
    from_ocpp,
    to_ocpp,
    utc_now_iso,
    validate,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# ─── Configuration ───────────────────────────────────────────────────────────

with open(_MODULE_DIR / 'config.json') as _config_file:
    CONFIG = json.load(_config_file)


def _cfg_path(key):
    path = Path(CONFIG[key])
    if path.is_absolute():
        return str(path)
    for base in (_MODULE_DIR, _PROJECT_ROOT, Path.cwd()):
        if (base / path).exists():
            return str((base / path).resolve())
    return str((_PROJECT_ROOT / path).resolve())


WSS_PORT = int(CONFIG['CSMS_WSS_PORT'])
TRIGGER_PORT = int(CONFIG['CSMS_TRIGGER_PORT'])
LOG_HTTPS_PORT = int(CONFIG['CSMS_LOG_HTTPS_PORT'])
LOG_UPLOAD_USER = CONFIG['LOG_UPLOAD_USER']
LOG_UPLOAD_PASSWORD = CONFIG['LOG_UPLOAD_PASSWORD']
MESSAGE_TIMEOUT = int(CONFIG['CSMS_MESSAGE_TIMEOUT'])
BASIC_AUTH_CP_PASSWORD = CONFIG['BASIC_AUTH_CP_PASSWORD']

SERVER_CERT = _cfg_path('CSMS_SERVER_CERT')
SERVER_KEY = _cfg_path('CSMS_SERVER_KEY')
SERVER_RSA_CERT = _cfg_path('CSMS_SERVER_RSA_CERT')
SERVER_RSA_KEY = _cfg_path('CSMS_SERVER_RSA_KEY')
CA_CERT = _cfg_path('CSMS_CA_CERT')
CA_KEY = _cfg_path('CSMS_CA_KEY')
V2G_ROOT_CERT = _cfg_path('V2G_ROOT_CERT')
V2G_SUB_CA_CERT = _cfg_path('V2G_SUB_CA_CERT')
V2G_SUB_CA_KEY = _cfg_path('V2G_SUB_CA_KEY')


# ─── Stations ────────────────────────────────────────────────────────────────

class Station:
    """What the CSMS knows about a Charging Station, across its connections."""

    def __init__(self, station_id, security_profile):
        self.id = station_id
        # The one security profile the station may connect with (A05.FR.07).
        self.security_profile = security_profile
        self.password = BASIC_AUTH_CP_PASSWORD
        # The next BootNotification is answered Pending (trigger API: set-pending-boot).
        self.pending_boot = False
        # The limits the station has reported, by (component, variable, instance), for
        # example ('DeviceDataCtrlr', 'ItemsPerMessage', 'GetVariables').
        self.limits = {}
        # The TxProfile charging profile the station accepted, by transaction id: the
        # SetChargingProfileRequest that set it.
        self.tx_profiles = {}
        # The transactions the CSMS has sent the limit of a prepaid card or ad hoc payment for.
        self.limited_transactions = set()
        # E16: limits that the CSMS has set for a transaction and still has to send, by
        # transaction id. Key None: for the ongoing or the next transaction of the station.
        self.limits_to_send = {}
        # The transactions with a cost limit.
        self.cost_limited = set()
        # K: the charging profiles that the station accepted, by id: the
        # SetChargingProfileRequest of each. And the last id the CSMS chose for a profile.
        self.charging_profiles = {}
        self._last_charging_profile_id = 0
        # What the CSMS knows of the station's device model: the values of variables, by
        # (component name, variable name, instance). The CSMS reads the ones it needs after a
        # boot (Session._learn_device_model), and keeps what it sets or gets reported.
        self.variables = {}
        # The ongoing transactions, by transaction id: the id of their EVSE, or None as long
        # as the station has not reported it.
        self.transactions = {}
        # K15 - K20: whether the CSMS provides a charging profile for the charging needs of
        # an EV (trigger API: provide-charging-profiles).
        self.provide_charging_profiles = True
        self._last_charging_schedule_id = 0
        # The ad hoc payments for which the CSMS started a transaction remotely, by PspRef:
        # the transactionLimit of each (C24.FR.02, C25.FR.24).
        self.payments = {}
        # The energy register (Wh) at the start of each transaction and its latest value, by
        # transaction id, for the central cost calculation.
        self.energy = {}
        self._last_remote_start_id = 0
        self.session = None

    def next_remote_start_id(self):
        self._last_remote_start_id += 1
        return self._last_remote_start_id

    def variable(self, component, name, instance=None):
        """The value of a variable of the station as the CSMS knows it, or None."""
        return self.variables.get((component, name, instance))

    def _flag(self, component, name, instance=None):
        value = self.variable(component, name, instance)
        return None if value is None else value.strip().lower() == 'true'

    @property
    def supported_limits(self):
        """TxCtrlr.SupportedLimits as a set; None when the CSMS does not know it."""
        value = self.variable('TxCtrlr', 'SupportedLimits')
        return None if value is None else {name.strip() for name in value.split(',') if name.strip()}

    @property
    def local_cost(self):
        """TariffCostCtrlr.Enabled[Cost]: the station calculates the cost of a transaction."""
        return self._flag('TariffCostCtrlr', 'Enabled', 'Cost')

    @property
    def max_external_constraints_id(self):
        try:
            return int(self.variable('SmartChargingCtrlr', 'MaxExternalConstraintsId'))
        except (TypeError, ValueError):
            return None

    @property
    def v2x_enabled(self):
        """ISO15118Ctrlr.Enabled and V2XChargingCtrlr.Enabled are both true (Q01.FR.01)."""
        return bool(self._flag('ISO15118Ctrlr', 'Enabled') and self._flag('V2XChargingCtrlr', 'Enabled'))

    def transaction_on(self, evse_id):
        """The id of the ongoing transaction on an EVSE: the latest one that the station
        reported for it, or else the latest one without a known EVSE."""
        for wanted in (evse_id, None):
            ids = [transaction_id for transaction_id, evse in self.transactions.items()
                   if evse == wanted]
            if ids:
                return ids[-1]
        return None

    def next_charging_schedule_id(self):
        self._last_charging_schedule_id += 1
        return self._last_charging_schedule_id

    def next_charging_profile_id(self):
        """An id for a charging profile that the CSMS makes. K01.FR.80: higher than
        MaxExternalConstraintsId, when the station has that variable."""
        self._last_charging_profile_id = max(
            self._last_charging_profile_id, self.max_external_constraints_id or 0,
            *self.charging_profiles) + 1
        return self._last_charging_profile_id

    def limit(self, component, variable, instance):
        return self.limits.get((component, variable, instance))


STATIONS = {
    station_id: Station(station_id, int(profile))
    for station_id, profile in CONFIG['STATIONS'].items()
}


# ─── ID tokens ───────────────────────────────────────────────────────────────

# idToken is an identifierString, which is case-insensitive.
ID_TOKENS = {token.upper(): dict(info) for token, info in CONFIG['ID_TOKENS'].items()}
GROUP_ID_TOKEN_TYPE = CONFIG['GROUP_ID_TOKEN_TYPE']


VALID_VAT_NUMBERS = {number.upper() for number in CONFIG['VALID_VAT_NUMBERS']}

# The receipts of ad hoc payments, by receipt id. The trigger API's HTTP server serves them at
# /receipts/<receipt id>.
RECEIPTS = {}

# The tariff of the central cost calculation: a price per kWh.
COST_PER_KWH = float(CONFIG['COST_PER_KWH'])

# Q01: the energy transfers that the CSMS allows an EV at a V2X capable station
ALLOWED_ENERGY_TRANSFER = CONFIG['ALLOWED_ENERGY_TRANSFER']
_BIDIRECTIONAL_ENERGY_TRANSFER = ('AC_BPT', 'AC_BPT_DER', 'DC_BPT', 'DC_ACDP_BPT')

# K15 - K20: the power (W) that the CSMS gives a transaction at most
SITE_POWER_LIMIT = float(CONFIG['SITE_POWER_LIMIT'])

# I08: the driver-specific tariffs, by idToken (upper case): a TariffType as on the wire
DRIVER_TARIFFS = {}

# TransactionLimitType: the fields, and their names in TxCtrlr.SupportedLimits
_LIMIT_NAMES = {'max_cost': 'maxCost', 'max_energy': 'maxEnergy', 'max_time': 'maxTime',
                'max_soc': 'maxSoC'}


# ─── Dynamic QR codes (C25) ──────────────────────────────────────────────────

QR_CODE_URL_TEMPLATE = CONFIG['QR_CODE_URL_TEMPLATE']
QR_CODE_SHARED_SECRET = CONFIG['QR_CODE_SHARED_SECRET']
QR_CODE_VALIDITY_TIME = int(CONFIG['QR_CODE_VALIDITY_TIME'])
QR_CODE_TOTP_LENGTH = int(CONFIG['QR_CODE_TOTP_LENGTH'])


def decode_qr_code_url(url):
    """The (station id, EVSE id, transaction limit) of the URL of a dynamic QR code. Raises
    ValueError when the URL is not valid."""
    import time
    from urllib.parse import parse_qs, urlsplit

    from payment import totp_v1

    template, given = urlsplit(QR_CODE_URL_TEMPLATE), urlsplit(url)
    if (given.scheme, given.netloc) != (template.scheme, template.netloc):
        raise ValueError('not a QR code URL of this CSMS')
    names = [segment.strip('{}') for segment in template.path.split('/') if segment]
    values = [segment for segment in given.path.split('/') if segment]
    if len(values) != len(names):
        # C25.FR.09: the URL has to have the parameters of the URL template
        raise ValueError('not all path parameters of the URL template are present')
    parameters = dict(zip(names, values))

    # C25.FR.07 and "Validation of TOTP": the one-time password of the current time interval,
    # or of the previous or the next one
    now = time.time()
    valid = {totp_v1(QR_CODE_SHARED_SECRET, QR_CODE_VALIDITY_TIME, QR_CODE_TOTP_LENGTH,
                     at=now + shift * QR_CODE_VALIDITY_TIME) for shift in (-1, 0, 1)}
    if parameters['totp'] not in valid:
        raise ValueError('the time-based one-time password is not valid')
    if parameters['version'] not in ('1', 'v1'):
        raise ValueError(f"unknown version of the one-time password: {parameters['version']}")
    if parameters['chargingstationid'] not in STATIONS:
        raise ValueError(f"unknown Charging Station: {parameters['chargingstationid']}")

    # C25.FR.59: the limits an EV Driver can ask for
    query = parse_qs(given.query)
    limit = {}
    if 'maxenergy' in query:
        limit['max_energy'] = float(query['maxenergy'][0])
    if 'maxtime' in query:
        limit['max_time'] = int(query['maxtime'][0])
    if 'maxcost' in query:
        limit['max_cost'] = float(query['maxcost'][0])
    return parameters['chargingstationid'], int(parameters['evse']), limit


def prepaid_balance(id_token):
    """The balance of the prepaid account of an idToken; None when it is not a prepaid card."""
    known = ID_TOKENS.get(id_token['id_token'].upper())
    return known.get('prepaid_balance') if known else None


def id_token_info(id_token):
    """The IdTokenInfoType the CSMS has for an idToken (a Payload or dict with snake_case
    fields)."""
    if id_token['type'] == 'NoAuthorization':
        # C02.FR.02
        return {'status': 'Accepted'}
    if id_token['type'] == 'DirectPayment':
        # An ad hoc payment that the payment service provider has authorized; the idToken is
        # its reference at the PSP (C18).
        return {'status': 'Accepted'}
    known = ID_TOKENS.get(id_token['id_token'].upper())
    if known is None:
        return {'status': 'Unknown'}
    info = {'status': known['status']}
    if known.get('group') and known['status'] == 'Accepted':
        info['group_id_token'] = {'id_token': known['group'], 'type': GROUP_ID_TOKEN_TYPE}
    if known['status'] == 'Accepted' and known.get('prepaid_balance') is not None:
        # C17.FR.01, C17.FR.02: a prepaid token does not remain in the authorization cache,
        # and it is only accepted with a positive balance.
        info['cache_expiry_date_time'] = utc_now_iso()
        if known['prepaid_balance'] <= 0:
            info['status'] = 'NoCredit'
    return info


# ─── Certificates ────────────────────────────────────────────────────────────

def sign_csr(csr_pem, certificate_type):
    """Sign a station's CSR and return the certificate chain as PEM (A02, A03).

    A Charging Station certificate is signed by the CSMS's CA (the Charging Station Operator
    hierarchy), and a V2G certificate by the sub-CA of the configured V2G chain.
    """
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization

    v2g = certificate_type in ('V2GCertificate', 'V2G20Certificate')
    issuer_cert_path, issuer_key_path = (V2G_SUB_CA_CERT, V2G_SUB_CA_KEY) if v2g else (CA_CERT, CA_KEY)
    with open(issuer_cert_path, 'rb') as f:
        issuer_cert = x509.load_pem_x509_certificate(f.read())
    with open(issuer_key_path, 'rb') as f:
        issuer_key = serialization.load_pem_private_key(f.read(), password=None)

    csr = x509.load_pem_x509_csr(csr_pem.encode())
    # The certificate is valid from a moment ago, for a station whose clock runs behind
    # (A02.FR.06 note).
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(issuer_cert.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=365))
        .sign(issuer_key, hashes.SHA256())
    )
    chain = certificate.public_bytes(serialization.Encoding.PEM).decode()
    chain += issuer_cert.public_bytes(serialization.Encoding.PEM).decode()
    return chain


# ─── ISO 15118 contract certificates (C07) ───────────────────────────────────

def _ocsp_query(responder_url, ocsp_request, serial_number):
    """POST an OCSP request (RFC 6960) and return the status the responder gives for the
    certificate: 'good', 'revoked' or 'unknown'. None when there is no usable answer."""
    import urllib.request
    from cryptography.hazmat.primitives import serialization
    from cryptography.x509 import ocsp

    http_request = urllib.request.Request(
        responder_url,
        data=ocsp_request.public_bytes(serialization.Encoding.DER),
        headers={'Content-Type': 'application/ocsp-request'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(http_request, timeout=5) as http_response:
            response = ocsp.load_der_ocsp_response(http_response.read())
    except Exception as error:
        logging.warning(f"OCSP responder {responder_url}: {error!r}")
        return None
    if response.response_status != ocsp.OCSPResponseStatus.SUCCESSFUL:
        logging.warning(f"OCSP responder {responder_url}: {response.response_status}")
        return None
    if response.serial_number != serial_number:
        return None
    return {
        ocsp.OCSPCertStatus.GOOD: 'good',
        ocsp.OCSPCertStatus.REVOKED: 'revoked',
        ocsp.OCSPCertStatus.UNKNOWN: 'unknown',
    }[response.certificate_status]


def _ocsp_result(request_data):
    """The OCSPResponse (RFC 6960) of the responder for OCSPRequestData: DER encoded, and then
    Base64 encoded. None when the responder gives no answer."""
    import base64
    import urllib.request
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.x509 import ocsp

    algorithm = {'SHA256': hashes.SHA256, 'SHA384': hashes.SHA384,
                 'SHA512': hashes.SHA512}[request_data.hash_algorithm]()
    ocsp_request = ocsp.OCSPRequestBuilder().add_certificate_by_hash(
        bytes.fromhex(request_data.issuer_name_hash), bytes.fromhex(request_data.issuer_key_hash),
        int(request_data.serial_number, 16), algorithm).build()
    http_request = urllib.request.Request(
        request_data.responder_url,
        data=ocsp_request.public_bytes(serialization.Encoding.DER),
        headers={'Content-Type': 'application/ocsp-request'}, method='POST')
    try:
        with urllib.request.urlopen(http_request, timeout=5) as http_response:
            return base64.b64encode(http_response.read()).decode('ascii')
    except Exception as error:
        logging.warning(f"OCSP responder {request_data.responder_url}: {error!r}")
        return None


def _cps_request(station_id, request):
    """POST a Get15118EVCertificate request to the certificate provisioning service proxy
    (CPS_PROXY_URL) and return its JSON answer, or None."""
    import urllib.request

    body = json.dumps({
        'stationId': station_id, 'chargePointId': station_id,
        'request': {name: value for name, value in request.items() if value is not None},
    }).encode()
    http_request = urllib.request.Request(
        CONFIG['CPS_PROXY_URL'], data=body, headers={'Content-Type': 'application/json'},
        method='POST')
    try:
        with urllib.request.urlopen(http_request, timeout=5) as http_response:
            return json.loads(http_response.read())
    except Exception as error:
        logging.warning(f"CPS proxy {CONFIG['CPS_PROXY_URL']}: {error!r}")
        return None


def _hash_data_statuses(hash_data):
    """The OCSP status of each certificate in iso15118CertificateHashData."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.x509 import ocsp

    algorithms = {'SHA256': hashes.SHA256(), 'SHA384': hashes.SHA384(), 'SHA512': hashes.SHA512()}
    statuses = []
    for entry in hash_data:
        try:
            serial_number = int(entry['serial_number'], 16)
            ocsp_request = ocsp.OCSPRequestBuilder().add_certificate_by_hash(
                bytes.fromhex(entry['issuer_name_hash']),
                bytes.fromhex(entry['issuer_key_hash']),
                serial_number,
                algorithms[entry['hash_algorithm']],
            ).build()
        except (ValueError, KeyError) as error:
            logging.warning(f"Unusable certificate hash data: {error!r}")
            statuses.append(None)
            continue
        statuses.append(_ocsp_query(entry['responder_url'], ocsp_request, serial_number))
    return statuses


def _certificate_chain_statuses(chain_pem):
    """The OCSP status of each certificate of a contract certificate chain, which has to lead
    to the configured V2G root. The responder is the one each certificate names (AIA)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.x509 import ocsp
    from cryptography.x509.oid import AuthorityInformationAccessOID, ExtensionOID

    try:
        chain = x509.load_pem_x509_certificates(chain_pem.encode())
        with open(V2G_ROOT_CERT, 'rb') as root_file:
            root = x509.load_pem_x509_certificate(root_file.read())
    except ValueError as error:
        logging.warning(f"Unusable contract certificate chain: {error!r}")
        return [None]

    statuses = []
    for index, certificate in enumerate(chain):
        if certificate == root:
            continue
        issuer = chain[index + 1] if index + 1 < len(chain) else root
        try:
            certificate.verify_directly_issued_by(issuer)
            access = certificate.extensions.get_extension_for_oid(
                ExtensionOID.AUTHORITY_INFORMATION_ACCESS).value
            responder_url = next(description.access_location.value for description in access
                                 if description.access_method == AuthorityInformationAccessOID.OCSP)
        except Exception as error:
            logging.warning(f"Contract certificate chain cannot be verified: {error!r}")
            statuses.append(None)
            continue
        ocsp_request = ocsp.OCSPRequestBuilder().add_certificate(
            certificate, issuer, hashes.SHA256()).build()
        statuses.append(_ocsp_query(responder_url, ocsp_request, certificate.serial_number))
    return statuses or [None]


def contract_certificate_authorization(token_info, statuses):
    """(certificateStatus, idTokenInfo) for an AuthorizeRequest with a contract certificate,
    from the OCSP status of each certificate of its chain."""
    if 'revoked' in statuses:
        # C07.FR.16
        return 'CertificateRevoked', {'status': 'Invalid'}
    if any(status != 'good' for status in statuses):
        # C07.FR.17: the chain cannot be verified
        return 'CertChainError', {'status': 'Invalid'}
    if token_info['status'] in ('Blocked', 'Expired', 'Invalid', 'Unknown'):
        # C07.FR.13: the certificate is valid, but the eMAID is not accepted
        return 'ContractCancelled', token_info
    # C07.FR.14
    return 'Accepted', token_info


# ─── A connection of a station ───────────────────────────────────────────────

class CallErrorReceived(Exception):
    """The station answered a request of the CSMS with a CALLERROR."""

    def __init__(self, code, description, details):
        self.code = code
        self.description = description
        self.details = details
        super().__init__(f"{code}: {description}")


class OcppError(Exception):
    """Raised by a request handler: the CSMS answers the request with a CALLERROR."""

    def __init__(self, code, description=''):
        self.code = code
        self.description = description
        super().__init__(f"{code}: {description}")


class Session:
    """One WebSocket connection of a station."""

    def __init__(self, station, websocket, security_profile):
        self.station = station
        self.id = station.id
        self._websocket = websocket
        self.security_profile = security_profile
        self._call_lock = asyncio.Lock()
        self._pending = {}
        self.boot_status = None

    # ─── Transport ───────────────────────────────────────────────────────────

    async def run(self):
        try:
            async for raw in self._websocket:
                await self._route(raw)
        except ConnectionClosed:
            pass
        finally:
            for pending in self._pending.values():
                if not pending.done():
                    pending.set_exception(ConnectionError('The station disconnected'))

    async def _send(self, message):
        logging.info(f"{self.id} <<< {json.dumps(message)}")
        await self._websocket.send(json.dumps(message, separators=(',', ':')))

    async def _route(self, raw):
        logging.info(f"{self.id} >>> {raw}")
        try:
            message = json.loads(raw)
            message_type, unique_id = message[0], message[1]
        except (ValueError, TypeError, IndexError, KeyError):
            # OCPP-J 2.1, 4.2.3: when the MessageId cannot be read, the CALLERROR has "-1".
            await self._send([CALL_ERROR, '-1', 'RpcFrameworkError', 'Not a valid RPC message', {}])
            return

        if message_type == CALL:
            asyncio.ensure_future(self._handle_call(unique_id, message))
        elif message_type in (CALL_RESULT, CALL_ERROR):
            pending = self._pending.get(unique_id)
            if pending is not None and not pending.done():
                pending.set_result(message)
        elif message_type == SEND:
            await self._handle_send(message)
        elif message_type == CALL_RESULT_ERROR:
            logging.error(f"{self.id}: the station could not process a response: {raw}")
        # Any other message type: the payload is ignored (OCPP-J 2.1, 4.1.3)

    async def call(self, action, payload, timeout=MESSAGE_TIMEOUT):
        """Send a request (payload as on the wire) and return the station's response payload."""
        unique_id = str(uuid.uuid4())
        pending = asyncio.get_running_loop().create_future()
        # A CALL is only sent once the one before it has been answered (OCPP-J 2.1, 4.1.1).
        async with self._call_lock:
            self._pending[unique_id] = pending
            try:
                await self._send([CALL, unique_id, action, payload])
                message = await asyncio.wait_for(pending, timeout)
            finally:
                self._pending.pop(unique_id, None)
        if message[0] == CALL_ERROR:
            raise CallErrorReceived(message[2], message[3], message[4] if len(message) > 4 else {})
        return message[2]

    async def request(self, action, data, timeout=MESSAGE_TIMEOUT):
        """Send a request given as snake_case data; return the response as a Payload.

        Tells the CSMS's own logic about the outcome (after_<Action>), like a request that
        the trigger API sends.
        """
        payload = to_ocpp(f'{action}Request', data)
        validate(f'{action}Request', payload)
        response = await self.call(action, payload, timeout)
        await self.after_call(action, payload, response)
        return from_ocpp(f'{action}Response', response)

    async def after_call(self, action, payload, response):
        """The station answered a request of the CSMS: update what the CSMS knows."""
        hook = getattr(self, f'after_{action}', None)
        if hook is not None:
            await hook(from_ocpp(f'{action}Request', payload),
                       from_ocpp(f'{action}Response', response))

    async def _handle_call(self, unique_id, message):
        try:
            action, payload = message[2], message[3]
        except IndexError:
            await self._send([CALL_ERROR, unique_id, 'RpcFrameworkError', 'Not a valid CALL', {}])
            return

        try:
            if action not in ACTIONS:
                raise OcppError('NotImplemented', f'{action} is not an OCPP 2.1 action')
            handler = getattr(self, f'on_{action}', None)
            if handler is None:
                raise OcppError('NotSupported', f'A CSMS does not handle {action}Request')
            try:
                validate(f'{action}Request', payload)
            except SchemaViolation as violation:
                raise OcppError(violation.error_code, '; '.join(violation.problems))
            self._check_registration(action)

            answer = handler(from_ocpp(f'{action}Request', payload))
            if asyncio.iscoroutine(answer):
                answer = await answer
            response = to_ocpp(f'{action}Response', answer or {})
            validate(f'{action}Response', response)
        except OcppError as error:
            await self._send([CALL_ERROR, unique_id, error.code, error.description[:255], {}])
            return
        except Exception as error:
            logging.exception(f"{self.id}: could not handle {message}")
            await self._send([CALL_ERROR, unique_id, 'InternalError', repr(error)[:255], {}])
            return

        await self._send([CALL_RESULT, unique_id, response])

    async def _handle_send(self, message):
        """An unconfirmed message: it gets no response, whatever it holds (OCPP-J 2.1, 4.2.4)."""
        action = message[2] if len(message) > 2 else None
        payload = message[3] if len(message) > 3 else None
        if action not in UNCONFIRMED_ACTIONS:
            logging.warning(f"{self.id}: SEND with an unknown action: {action}")
            return
        try:
            validate(action, payload)
        except SchemaViolation as violation:
            logging.warning(f"{self.id}: {violation}")
            return
        handler = getattr(self, f'on_{action}', None)
        if handler is not None:
            handler(from_ocpp(action, payload))

    def _check_registration(self, action):
        """B02.FR.09, B03.FR.07: until the CSMS has accepted the station, a request other than
        BootNotificationRequest is answered with a CALLERROR SecurityError."""
        if action != 'BootNotification' and self.boot_status in ('Pending', 'Rejected'):
            raise OcppError('SecurityError',
                            f'{action} is not allowed while the registration is {self.boot_status}')

    def later(self, coroutine):
        """Run something the CSMS does on its own, after the current response."""
        async def run():
            try:
                await coroutine
            except (ConnectionError, ConnectionClosed, asyncio.TimeoutError, CallErrorReceived) as error:
                logging.warning(f"{self.id}: {error!r}")
            except Exception:
                logging.exception(f"{self.id}: CSMS action failed")
        return asyncio.ensure_future(run())

    # ─── B: Provisioning ─────────────────────────────────────────────────────

    def on_BootNotification(self, request):
        self.boot_status = 'Pending' if self.station.pending_boot else 'Accepted'
        # The station has (re)started: what the CSMS has read from its device model may no
        # longer hold, and a limit that waited for its next transaction is dropped.
        self.station.variables.clear()
        self.station.limits_to_send.pop(None, None)
        if self.boot_status == 'Accepted':
            self.later(self._learn_device_model())
        return {
            'current_time': utc_now_iso(),
            'interval': 5 if self.boot_status == 'Pending' else 300,
            'status': self.boot_status,
        }

    def on_StatusNotification(self, request):
        return {}

    def on_NotifyEvent(self, request):
        return {}

    def on_Heartbeat(self, request):
        return {'current_time': utc_now_iso()}

    _LIMIT_VARIABLES = ('ItemsPerMessage', 'BytesPerMessage')

    def _remember_limit(self, component, variable, value):
        """Keep a limit the station reports, such as DeviceDataCtrlr.ItemsPerMessage
        [GetVariables] (B06.FR.05) or MonitoringCtrlr.ItemsPerMessage
        [ClearVariableMonitoring] (N06.FR.04)."""
        if variable.name in self._LIMIT_VARIABLES and value is not None:
            try:
                self.station.limits[(component.name, variable.name, variable.instance)] = int(value)
            except ValueError:
                pass

    # The variables that the CSMS reads after a boot: (component, variable, instance)
    _DEVICE_MODEL = (
        ('TxCtrlr', 'SupportedLimits', None),                    # E16.FR.12
        ('TariffCostCtrlr', 'Enabled', 'Cost'),                  # E16.FR.11
        ('SmartChargingCtrlr', 'MaxExternalConstraintsId', None),    # K01.FR.80
        ('ISO15118Ctrlr', 'Enabled', None),                      # Q01.FR.01
        ('V2XChargingCtrlr', 'Enabled', None),                   # Q01.FR.01
    )

    async def _learn_device_model(self):
        """Read what the CSMS has to know of the device model of a station that has booted."""
        await self.request('GetVariables', {'get_variable_data': [
            {'component': {'name': component},
             'variable': {'name': name} if instance is None else {'name': name, 'instance': instance}}
            for component, name, instance in self._DEVICE_MODEL
        ]})

    def _remember_variable(self, component, variable, value):
        """Keep what the station tells about its device model."""
        self._remember_limit(component, variable, value)
        if value is not None:
            self.station.variables[(component.name, variable.name, variable.instance)] = value

    async def after_GetVariables(self, request, response):
        for result in response.get_variable_result:
            if result.attribute_status == 'Accepted' and result.attribute_type in (None, 'Actual'):
                self._remember_variable(result.component, result.variable, result.attribute_value)

    async def after_SetVariables(self, request, response):
        accepted = {(result.component.name, result.variable.name, result.variable.instance)
                    for result in response.set_variable_result
                    if result.attribute_status == 'Accepted'}
        for data in request.set_variable_data:
            if (data.attribute_type in (None, 'Actual') and
                    (data.component.name, data.variable.name, data.variable.instance) in accepted):
                self._remember_variable(data.component, data.variable, data.attribute_value)

    def on_NotifyReport(self, request):
        for data in request.report_data or []:
            for attribute in data.variable_attribute:
                if attribute.type in (None, 'Actual'):
                    self._remember_variable(data.component, data.variable, attribute.value)
        return {}

    # ─── C: Authorization ────────────────────────────────────────────────────

    async def on_Authorize(self, request):
        response = await self._authorize(request)
        tariff = DRIVER_TARIFFS.get(request.id_token.id_token.upper())
        accepted = response['id_token_info']['status'] == 'Accepted'
        if tariff is not None and accepted:
            # I08.FR.01: the driver-specific tariff of an idToken that is accepted for charging
            response['tariff'] = tariff
        if accepted and self.station.v2x_enabled:
            # Q01.FR.01: the energy transfers that are allowed for this EV
            response['allowed_energy_transfer'] = list(ALLOWED_ENERGY_TRANSFER)
        return response

    async def _authorize(self, request):
        token_info = id_token_info(request.id_token)
        if request.iso15118_certificate_hash_data is None and request.certificate is None:
            return {'id_token_info': token_info}

        # C07.FR.05: the CSMS verifies the certificate and its chain via OCSP.
        if request.iso15118_certificate_hash_data is not None:
            statuses = await asyncio.to_thread(
                _hash_data_statuses, request.iso15118_certificate_hash_data)
        else:
            statuses = await asyncio.to_thread(_certificate_chain_statuses, request.certificate)
        certificate_status, token_info = contract_certificate_authorization(token_info, statuses)
        return {'id_token_info': token_info, 'certificate_status': certificate_status}

    def on_VatNumberValidation(self, request):
        """C18.FR.09, C18.FR.10: Accepted for a valid VAT number, with the evseId of the
        request."""
        valid = request.vat_number.upper() in VALID_VAT_NUMBERS
        return {
            'vat_number': request.vat_number,
            'evse_id': request.evse_id,
            'status': 'Accepted' if valid else 'Rejected',
        }

    def on_NotifySettlement(self, request):
        """C21.FR.03: when the station settled the payment and leaves the receipt to the CSMS
        (it sends no receiptUrl), the CSMS answers with the URL of the receipt."""
        if request.status != 'Settled' or request.receipt_url is not None:
            return {}
        receipt_id = str(uuid.uuid4())
        RECEIPTS[receipt_id] = {
            'pspRef': request.psp_ref,
            'transactionId': request.transaction_id,
            'amount': request.settlement_amount,
            'time': request.settlement_time,
        }
        return {'receipt_id': receipt_id,
                'receipt_url': f"http://localhost:{TRIGGER_PORT}/receipts/{receipt_id}"}

    # ─── E: Transactions ─────────────────────────────────────────────────────

    def on_TransactionEvent(self, request):
        station = self.station
        transaction_id = request.transaction_info.transaction_id
        reported_limit = request.transaction_info.transaction_limit
        response = {}
        limit = {}
        if request.id_token is not None:
            # E01.FR.12: the authorization status, and the groupIdToken if one exists
            response['id_token_info'] = id_token_info(request.id_token)
            if transaction_id not in station.limited_transactions:
                if prepaid_balance(request.id_token):
                    # C17.FR.03: (only one time) the maximum amount that may be spent
                    limit = {'max_cost': prepaid_balance(request.id_token)}
                elif request.id_token.type == 'DirectPayment':
                    # C24.FR.02, C25.FR.24: the limit of the ad hoc payment
                    limit = dict(station.payments.get(request.id_token.id_token) or {})
                if limit:
                    station.limited_transactions.add(transaction_id)

        # E16.FR.02: a limit that the CSMS has set for the transaction goes, once, into the
        # first possible TransactionEventResponse.
        for key in (transaction_id, None):
            limit.update(station.limits_to_send.pop(key, None) or {})
        if station.supported_limits is not None:
            # E16.FR.12: only the limits that the station has in TxCtrlr.SupportedLimits
            limit = {name: value for name, value in limit.items()
                     if _LIMIT_NAMES[name] in station.supported_limits}
        if reported_limit is not None:
            # E16.FR.08: no limit in the response when the limit that the station reports
            # is lower than or equal to the one the CSMS requires
            limit = {name: value for name, value in limit.items()
                     if reported_limit[name] is None or reported_limit[name] > value}
        if limit:
            response['transaction_limit'] = limit
        if 'max_cost' in limit or (reported_limit is not None and reported_limit.max_cost is not None):
            station.cost_limited.add(transaction_id)

        if request.evse is not None:
            station.transactions[transaction_id] = request.evse.id
        else:
            station.transactions.setdefault(transaction_id, None)

        self._track_energy(transaction_id, request.meter_value)
        # The station calculates the cost itself when it says so in TariffCostCtrlr.Enabled
        # [Cost], or when it reports the cost in costDetails. Otherwise the CSMS does.
        central_cost = request.cost_details is None and station.local_cost is not True
        if central_cost and (request.event_type == 'Ended' or request.meter_value
                             or transaction_id in station.cost_limited):
            # I02.FR.01: the running cost, with every meter value; E16.FR.11: cost updates
            # for a transaction with a cost limit; I03.FR.02: the final total cost when the
            # transaction has ended
            response['total_cost'] = self._energy_cost(transaction_id)
            if (request.trigger_reason == 'LimitSet' and reported_limit is not None
                    and reported_limit.max_cost is not None):
                # The station confirmed the cost limit: from here it needs the running cost.
                self.later(self.request('CostUpdated', {
                    'total_cost': self._energy_cost(transaction_id),
                    'transaction_id': transaction_id,
                }))

        if request.trigger_reason == 'TxResumed' and transaction_id in station.tx_profiles:
            # B13.FR.31: the CSMS sends the TxProfile of a resumed transaction again.
            self.later(self.request('SetChargingProfile', station.tx_profiles[transaction_id]))
        if request.event_type == 'Ended':
            station.tx_profiles.pop(transaction_id, None)
            station.transactions.pop(transaction_id, None)
            station.cost_limited.discard(transaction_id)
            station.limits_to_send.pop(transaction_id, None)
        return response

    def _track_energy(self, transaction_id, meter_values):
        """Keep the first and the latest reading of the energy register of a transaction."""
        for meter_value in meter_values or []:
            for sampled in meter_value.sampled_value:
                if sampled.measurand not in (None, 'Energy.Active.Import.Register'):
                    continue
                unit = sampled.unit_of_measure.unit if sampled.unit_of_measure else None
                reading = sampled.value * (1000 if unit == 'kWh' else 1)
                first, _ = self.station.energy.get(transaction_id, (reading, reading))
                self.station.energy[transaction_id] = (first, reading)

    def _energy_cost(self, transaction_id):
        first, latest = self.station.energy.get(transaction_id, (0, 0))
        return round((latest - first) / 1000 * COST_PER_KWH, 2)

    # ─── K: Smart Charging ───────────────────────────────────────────────────

    async def after_SetChargingProfile(self, request, response):
        if response.status != 'Accepted':
            return
        profile = request.charging_profile
        self.station.charging_profiles[profile.id] = request
        if profile.charging_profile_purpose == 'TxProfile' and profile.transaction_id is not None:
            self.station.tx_profiles[profile.transaction_id] = request

    async def after_ClearChargingProfile(self, request, response):
        if response.status != 'Accepted':
            return
        profiles = self.station.charging_profiles
        if request.charging_profile_id is not None:
            profiles.pop(request.charging_profile_id, None)
            return
        criteria = request.charging_profile_criteria
        for profile_id, stored in list(profiles.items()):
            profile = stored.charging_profile
            if criteria is None or (
                    criteria.evse_id in (None, stored.evse_id)
                    and criteria.charging_profile_purpose in (None, profile.charging_profile_purpose)
                    and criteria.stack_level in (None, profile.stack_level)):
                del profiles[profile_id]

    # ─── K15 - K20: ISO 15118 smart charging ─────────────────────────────────

    def on_NotifyEVChargingNeeds(self, request):
        station = self.station
        needs = request.charging_needs
        transaction_id = station.transaction_on(request.evse_id)
        iso15118_20 = needs.control_mode is not None or needs.v2x_charging_parameters is not None
        if transaction_id is None:
            return {'status': 'Rejected',
                    'status_info': {'reason_code': 'TxNotFound',
                                    'additional_info': f'No transaction on EVSE {request.evse_id}'}}
        if station.v2x_enabled and needs.requested_energy_transfer not in ALLOWED_ENERGY_TRANSFER:
            # K18.FR.22, K19.FR.15: the CSMS does not accept the requested energy transfer
            return {'status': 'Rejected'}
        if not station.provide_charging_profiles:
            # K18.FR.04, K19.FR.04 for ISO 15118-20; K15.FR.04 for ISO 15118-2
            return {'status': 'NoChargingProfile' if iso15118_20 else 'Rejected'}
        # K15.FR.07, K17.FR.07, K18.FR.07, K19.FR.07: a TxProfile for the transaction
        self.later(self.request('SetChargingProfile',
                                self._ev_charging_profile(request, transaction_id)))
        return {'status': 'Accepted'}

    def _ev_charging_profile(self, request, transaction_id):
        """The SetChargingProfileRequest that answers the charging needs of an EV: one
        charging schedule with one period, which gives the EV the power that it can take, up
        to the limit of the site."""
        station = self.station
        needs = request.charging_needs
        power = None
        if needs.v2x_charging_parameters is not None:
            power = needs.v2x_charging_parameters.max_charge_power
        elif needs.ac_charging_parameters is not None:
            ac = needs.ac_charging_parameters
            phases = {'AC_single_phase': 1, 'AC_two_phase': 2}.get(needs.requested_energy_transfer, 3)
            power = ac.ev_max_current * ac.ev_max_voltage * phases
        elif needs.dc_charging_parameters is not None:
            dc = needs.dc_charging_parameters
            power = dc.ev_max_power or dc.ev_max_current * dc.ev_max_voltage
        limit = min(power, SITE_POWER_LIMIT) if power else SITE_POWER_LIMIT
        period = {'start_period': 0, 'limit': limit}
        if needs.requested_energy_transfer in _BIDIRECTIONAL_ENERGY_TRANSFER:
            # Q03.FR.01: the CSMS gives the setpoint for charging and discharging
            period.update(operation_mode='CentralSetpoint', setpoint=limit)
            discharge = needs.v2x_charging_parameters.max_discharge_power \
                if needs.v2x_charging_parameters is not None else None
            if discharge:
                period['discharge_limit'] = -min(discharge, SITE_POWER_LIMIT)
        # K01.FR.39: one TxProfile per stack level for a transaction, so a new profile for the
        # transaction replaces the one that it has (K01.FR.05).
        current = station.tx_profiles.get(transaction_id)
        return {
            'evse_id': request.evse_id,
            'charging_profile': {
                'id': current.charging_profile.id if current else station.next_charging_profile_id(),
                'stack_level': current.charging_profile.stack_level if current else 0,
                'charging_profile_purpose': 'TxProfile',
                'charging_profile_kind': 'Absolute',
                'transaction_id': transaction_id,
                'charging_schedule': [{
                    'id': station.next_charging_schedule_id(),
                    'start_schedule': utc_now_iso(),
                    'charging_rate_unit': 'W',
                    'charging_schedule_period': [period],
                }],
            },
        }

    def on_NotifyEVChargingSchedule(self, request):
        station = self.station
        transaction_id = station.transaction_on(request.evse_id)
        current = station.tx_profiles.get(transaction_id)
        if current is None or self._within_limits(request.charging_schedule, current.charging_profile):
            # K15.FR.11, K16.FR.06, K17.FR.11, K18.FR.11
            return {'status': 'Accepted'}
        # K15.FR.12/13, K16.FR.07/08, K17.FR.12/13, K18.FR.12/13: not within the limits of the
        # charging schedule of the CSMS: Rejected, and a new renegotiation (K16).
        self.later(self.request('SetChargingProfile', dict(current)))
        return {'status': 'Rejected'}

    @staticmethod
    def _within_limits(ev_schedule, profile):
        """Whether the charging schedule of an EV stays within one of the charging schedules
        of a charging profile of the CSMS."""
        def limit_at(periods, moment):
            active = [period for period in periods if period.start_period <= moment]
            period = active[-1] if active else periods[0]
            return period.limit if period.limit is not None else period.setpoint

        for schedule in profile.charging_schedule:
            if schedule.charging_rate_unit != ev_schedule.charging_rate_unit:
                continue
            if all(limit_at(schedule.charging_schedule_period, period.start_period) is None
                   or (period.limit if period.limit is not None else period.setpoint or 0)
                   <= limit_at(schedule.charging_schedule_period, period.start_period) + 1e-6
                   for period in ev_schedule.charging_schedule_period):
                return True
        return False

    def on_NotifyChargingLimit(self, request):
        return {}

    def on_ClearedChargingLimit(self, request):
        return {}

    def on_ReportChargingProfiles(self, request):
        return {}

    def on_NotifyPriorityCharging(self, request):
        return {}

    def on_PullDynamicScheduleUpdate(self, request):
        stored = self.station.charging_profiles.get(request.charging_profile_id)
        if stored is None or stored.charging_profile.charging_profile_kind != 'Dynamic':
            # K28.FR.12
            return {'status': 'Rejected', 'status_info': {'reason_code': 'InvalidProfile'}}
        # K28.FR.07: the limits/setpoints to use in the charging profile
        period = stored.charging_profile.charging_schedule[0].charging_schedule_period[0]
        update = {name: period[name] for name in ('limit', 'setpoint', 'discharge_limit')
                  if period[name] is not None}
        return {'status': 'Accepted', 'schedule_update': update or {'limit': 0.0}}

    def on_MeterValues(self, request):
        return {}

    # ─── A: Security ─────────────────────────────────────────────────────────

    # ─── N: Diagnostics ──────────────────────────────────────────────────────

    def on_NotifyMonitoringReport(self, request):
        return {}

    def on_NotifyCustomerInformation(self, request):
        return {}

    def on_OpenPeriodicEventStream(self, request):
        return {'status': 'Accepted'}

    def on_ClosePeriodicEventStream(self, request):
        return {}

    # ─── P, R, S: Data transfer, DER control, battery swapping ───────────────

    def on_DataTransfer(self, request):
        # P02.FR.06: the CSMS has no implementation for the vendorId
        return {'status': 'UnknownVendorId'}

    def on_ReportDERControl(self, request):
        return {}

    def on_NotifyDERAlarm(self, request):
        return {}

    def on_NotifyDERStartStop(self, request):
        return {}

    def on_BatterySwap(self, request):
        return {}

    # ─── O: Display messages ─────────────────────────────────────────────────

    def on_NotifyDisplayMessages(self, request):
        return {}

    # ─── H: Reservation ──────────────────────────────────────────────────────

    def on_ReservationStatusUpdate(self, request):
        return {}

    # ─── L, N: Firmware and log status ───────────────────────────────────────

    def on_FirmwareStatusNotification(self, request):
        return {}

    def on_LogStatusNotification(self, request):
        return {}

    def on_PublishFirmwareStatusNotification(self, request):
        return {}

    # ─── M: Certificate management ───────────────────────────────────────────

    async def on_GetCertificateStatus(self, request):
        """M06: the CSMS asks the OCSP responder, and passes its answer on."""
        result = await asyncio.to_thread(_ocsp_result, request.ocsp_request_data)
        if result is None:
            return {'status': 'Failed'}
        return {'status': 'Accepted', 'ocsp_result': result}

    async def on_Get15118EVCertificate(self, request):
        """M01, M02: the CSMS forwards the request of the EV to the provisioning service."""
        answer = await asyncio.to_thread(_cps_request, self.id, {
            'action': request.action,
            'iso15118SchemaVersion': request.iso15118_schema_version,
            'exiRequest': request.exi_request,
            'maximumContractCertificateChains': request.maximum_contract_certificate_chains,
            'prioritizedEMAIDs': request.prioritized_emaids,
        })
        if answer is None or answer.get('status') != 'Accepted':
            return {'status': 'Failed', 'exi_response': ''}
        response = {'status': 'Accepted', 'exi_response': answer['exiResponse']}
        if answer.get('remainingContracts') is not None:
            response['remaining_contracts'] = answer['remainingContracts']
        return response

    def on_SecurityEventNotification(self, request):
        return {}

    def on_SignCertificate(self, request):
        """A02.FR.11: Accepted when the CSMS can process the CSR. The signed certificate
        follows in a CertificateSignedRequest."""
        try:
            chain = sign_csr(request.csr, request.certificate_type)
        except Exception as error:
            logging.warning(f"{self.id}: the CSR cannot be processed: {error!r}")
            return {'status': 'Rejected'}

        async def send_certificate():
            await asyncio.sleep(0.2)
            await self.request('CertificateSigned', {
                'certificate_chain': chain,
                # A02.FR.14: the type of certificate in the SignCertificateRequest
                'certificate_type': request.certificate_type,
                # A02.FR.25: the requestId of the SignCertificateRequest
                'request_id': request.request_id,
            })

        self.later(send_certificate())
        return {'status': 'Accepted'}


# ─── WebSocket server ────────────────────────────────────────────────────────

def _unauthorized():
    return (
        http.HTTPStatus.UNAUTHORIZED,
        [('WWW-Authenticate', 'Basic realm="Access to CSMS"')],
        b'HTTP 401 Unauthorized\n',
    )


def _decode_basic_auth(auth_header):
    """Decode a Basic auth header. Returns (username, password) or None."""
    if not auth_header or not auth_header.startswith('Basic '):
        return None
    try:
        decoded = base64.b64decode(auth_header.split(' ', 1)[1]).decode('utf-8')
        username, password = decoded.split(':', 1)
        return username, password
    except (ValueError, UnicodeDecodeError):
        return None


class StationProtocol(WebSocketServerProtocol):
    """Decides, before the WebSocket upgrade, whether a station may connect."""

    async def process_request(self, path, request_headers):
        station_id = path.strip('/')
        station = STATIONS.get(station_id)
        if station is None:
            # OCPP-J 2.1, 3.3: an unknown station identifier gets HTTP 404.
            logging.warning(f"Unknown station {station_id!r}")
            return http.HTTPStatus.NOT_FOUND, [], b'Unknown Charging Station\n'

        ssl_object = self.transport.get_extra_info('ssl_object')
        client_certificate = ssl_object.getpeercert() if ssl_object is not None else None
        credentials = _decode_basic_auth(request_headers.get('Authorization'))

        if station.security_profile == 3:
            # TLS with a client side certificate. The TLS handshake has verified the
            # certificate against the CSMS's CA.
            if not client_certificate or credentials is not None:
                logging.warning(f"{station_id}: security profile 3 needs a client certificate "
                                f"and no Basic Auth")
                return _unauthorized()
        else:
            # Basic Auth (A00.FR.204: the username equals the station's identity).
            if client_certificate or credentials is None:
                logging.warning(f"{station_id}: security profile {station.security_profile} "
                                f"needs Basic Auth")
                return _unauthorized()
            username, password = credentials
            if username != station_id or not secrets.compare_digest(password, station.password):
                logging.warning(f"{station_id}: wrong Basic Auth credentials")
                return _unauthorized()
        return None


async def on_connect(websocket, path):
    station = STATIONS[path.strip('/')]
    if websocket.subprotocol != SUBPROTOCOL:
        # OCPP-J 2.1, 3.3: when the CSMS does not agree to one of the offered subprotocols, it
        # completes the handshake without a Sec-WebSocket-Protocol header and then
        # immediately closes the connection.
        logging.warning(f"{station.id}: no supported subprotocol offered; closing")
        await websocket.close()
        return

    session = Session(station, websocket, station.security_profile)
    previous = station.session
    station.session = session
    if previous is not None:
        # A station has one connection: the new one replaces the old one.
        asyncio.ensure_future(previous._websocket.close())
    logging.info(f"{station.id}: connected (security profile {station.security_profile})")
    try:
        await session.run()
    finally:
        if station.session is session:
            station.session = None
        logging.info(f"{station.id}: disconnected")


def create_server_ssl_context():
    """Create the SSL context of the WSS server.

    Loads both the ECDSA and the RSA server certificate, so that OpenSSL picks the one that
    fits the negotiated cipher suite (A00.FR.318: the TLS_ECDHE_ECDSA suites use the EC
    certificate, the TLS_RSA suites the RSA certificate).
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # A00.FR.314 / A00.FR.416: TLS 1.2 or higher
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    # The RSA key exchange suites of A00.FR.318 are off at OpenSSL's default security level.
    ctx.set_ciphers('DEFAULT:AES128-GCM-SHA256:AES256-GCM-SHA384:@SECLEVEL=1')
    ctx.load_cert_chain(certfile=SERVER_CERT, keyfile=SERVER_KEY)
    ctx.load_cert_chain(certfile=SERVER_RSA_CERT, keyfile=SERVER_RSA_KEY)
    # A client certificate is optional at the TLS level, because Basic Auth stations use the
    # same endpoint. One that is presented must be issued by the CSMS's CA.
    ctx.load_verify_locations(cafile=CA_CERT)
    ctx.verify_mode = ssl.CERT_OPTIONAL
    return ctx


# ─── HTTP trigger API ────────────────────────────────────────────────────────
# Lightweight TCP-based HTTP server (no extra dependencies). The tests POST to these endpoints
# to make the CSMS send OCPP messages to a station: the Manual Actions of the test cases.

class TriggerError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


def _session(station_id):
    station = STATIONS.get(station_id)
    if station is None:
        raise TriggerError(404, f'Unknown station {station_id}')
    if station.session is None:
        raise TriggerError(409, f'Station {station_id} is not connected')
    return station.session


async def _relay(session, action, payload):
    """Send a request to the station and report its answer as the trigger API's answer."""
    try:
        validate(f'{action}Request', payload)
    except SchemaViolation as violation:
        raise TriggerError(400, str(violation))
    try:
        response = await session.call(action, payload)
    except CallErrorReceived as error:
        return {'error': {'code': error.code, 'description': error.description,
                          'details': error.details}}
    except asyncio.TimeoutError:
        return {'result': 'timeout'}
    except (ConnectionError, ConnectionClosed) as error:
        return {'result': 'disconnected', 'message': str(error)}
    await session.after_call(action, payload, response)
    return response


async def _trigger_call(station_id, action, body):
    """call/{Action}: send that request, with the body as its payload."""
    if action not in ACTIONS:
        raise TriggerError(400, f'{action} is not an OCPP 2.1 action')
    session = _session(station_id)
    if action == 'SetChargingProfile' and isinstance(body.get('chargingProfile'), dict) \
            and 'id' not in body['chargingProfile']:
        # The CSMS chooses the id of a charging profile that comes without one (K01.FR.80).
        body = dict(body, chargingProfile=dict(
            body['chargingProfile'], id=session.station.next_charging_profile_id()))
    return await _relay(session, action, body)


async def _trigger_message(station_id, body):
    """trigger-message: send a TriggerMessageRequest."""
    return await _relay(_session(station_id), 'TriggerMessage', body)


def _new_password():
    """A01.FR.07: a random password; passwordString of 16 to 40 characters."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


async def _trigger_update_basic_auth_password(station_id, body):
    """update-basic-auth-password: set a new Basic Auth password on the station (A01)."""
    session = _session(station_id)
    new_password = _new_password()
    answer = await _relay(session, 'SetVariables', {'setVariableData': [{
        'component': {'name': 'SecurityCtrlr'},
        'variable': {'name': 'BasicAuthPassword'},
        'attributeValue': new_password,
    }]})
    results = answer.get('setVariableResult') or [{}]
    if results[0].get('attributeStatus') == 'Accepted':
        # A01.FR.03: the credentials used before are no longer accepted.
        session.station.password = new_password
    # A01.FR.04: with any other status the old credentials stay valid.
    return answer


async def _trigger_set_basic_auth_password(body):
    """/api/octt/set-basic-auth-password: store a password for a station. No OCPP message."""
    station = STATIONS.get(body.get('station_id'))
    if station is None or body.get('password') is None:
        raise TriggerError(400, 'Missing or unknown station_id, or missing password')
    station.password = body['password']
    return {'ok': True}


async def _trigger_set_security_profile(station_id, body):
    """set-security-profile: the station now uses this profile, as after a completed upgrade,
    and lower profiles are refused (A05.FR.07). No OCPP message."""
    station = STATIONS.get(station_id)
    if station is None or body.get('security_profile') is None:
        raise TriggerError(400, 'Unknown station, or missing security_profile')
    station.security_profile = int(body['security_profile'])
    return {'ok': True}


async def _trigger_set_pending_boot(station_id, body):
    """set-pending-boot: answer the station's next BootNotifications with Pending (true) or
    Accepted (false). No OCPP message."""
    station = STATIONS.get(station_id)
    if station is None:
        raise TriggerError(404, f'Unknown station {station_id}')
    station.pending_boot = bool(body.get('pending', True))
    return {'ok': True}


async def _batched(session, action, list_field, result_field, items, limit):
    """Send the items in as many requests as the station's ItemsPerMessage limit requires."""
    size = limit if limit and limit > 0 else max(len(items), 1)
    results = []
    for start in range(0, len(items), size):
        answer = await _relay(session, action, {list_field: items[start:start + size]})
        results.extend(answer.get(result_field, []))
    return {result_field: results}


async def _trigger_get_variables(station_id, body):
    """get-variables: GetVariablesRequest(s), split by ItemsPerMessageGetVariables (B06.FR.05)."""
    session = _session(station_id)
    return await _batched(session, 'GetVariables', 'getVariableData', 'getVariableResult',
                          body.get('getVariableData', []),
                          session.station.limit('DeviceDataCtrlr', 'ItemsPerMessage', 'GetVariables'))


async def _trigger_set_variables(station_id, body):
    """set-variables: SetVariablesRequest(s), split by ItemsPerMessageSetVariables (B05.FR.11)."""
    session = _session(station_id)
    return await _batched(session, 'SetVariables', 'setVariableData', 'setVariableResult',
                          body.get('setVariableData', []),
                          session.station.limit('DeviceDataCtrlr', 'ItemsPerMessage', 'SetVariables'))


_NETWORK_CONFIGURATION_VARIABLES = (
    ('ocppCsmsUrl', 'OcppCsmsUrl'),
    ('ocppInterface', 'OcppInterface'),
    ('ocppTransport', 'OcppTransport'),
    ('ocppVersion', 'OcppVersion'),
    ('messageTimeout', 'MessageTimeout'),
    ('securityProfile', 'SecurityProfile'),
    ('identity', 'Identity'),
    ('basicAuthPassword', 'BasicAuthPassword'),
)
_VPN_VARIABLES = (
    ('type', 'VpnType'),
    ('server', 'VpnServer'),
    ('user', 'VpnUser'),
    ('group', 'VpnGroup'),
    ('password', 'VpnPassword'),
    ('key', 'VpnKey'),
)
_APN_VARIABLES = (
    ('apn', 'Apn'),
    ('apnUserName', 'ApnUserName'),
    ('apnPassword', 'ApnPassword'),
    ('simPin', 'SimPin'),
    ('preferredNetwork', 'PreferredNetwork'),
    ('useOnlyPreferredNetwork', 'UseOnlyPreferredNetwork'),
    ('apnAuthentication', 'ApnAuthentication'),
)


def _variable_value(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)


async def _trigger_set_network_configuration(station_id, body):
    """set-network-configuration: set a network configuration through the device model
    (B09, "Setting network configuration via device model"). The body is that of a
    SetNetworkProfileRequest. The CSMS sends SetVariablesRequest(s) for the variables of the
    component NetworkConfiguration with instance <configurationSlot>."""
    session = _session(station_id)
    try:
        validate('SetNetworkProfileRequest', body)
    except SchemaViolation as violation:
        raise TriggerError(400, str(violation))
    component = {'name': 'NetworkConfiguration', 'instance': str(body['configurationSlot'])}
    data = body['connectionData']
    apn, vpn = data.get('apn'), data.get('vpn')

    def variables(source, names):
        return [
            {'component': component, 'variable': {'name': variable},
             'attributeValue': _variable_value(source[field])}
            for field, variable in names if field in source
        ]

    def flag(variable, enabled):
        return {'component': component, 'variable': {'name': variable},
                'attributeValue': _variable_value(enabled)}

    set_variable_data = variables(data, _NETWORK_CONFIGURATION_VARIABLES)
    # B09.FR.29, B09.FR.30: VpnEnabled / ApnEnabled is True when the CSMS configures variables
    # for a VPN / APN connection, and False when it does not.
    set_variable_data.append(flag('VpnEnabled', vpn is not None))
    set_variable_data += variables(vpn or {}, _VPN_VARIABLES)
    set_variable_data.append(flag('ApnEnabled', apn is not None))
    set_variable_data += variables(apn or {}, _APN_VARIABLES)

    return await _batched(session, 'SetVariables', 'setVariableData', 'setVariableResult',
                          set_variable_data,
                          session.station.limit('DeviceDataCtrlr', 'ItemsPerMessage', 'SetVariables'))


async def _trigger_set_transaction_limit(station_id, body):
    """set-transaction-limit: the CSMS sets or changes a limit in cost, energy, time or SoC
    for a transaction of this station (E16): the transaction of transactionId, or without it
    the ongoing or else the next transaction. The CSMS sends the limit in the first possible
    TransactionEventResponse (E16.FR.02)."""
    session = _session(station_id)
    limit = {name: body[field] for name, field in _LIMIT_NAMES.items() if body.get(field) is not None}
    if not limit:
        raise TriggerError(400, 'one of maxCost, maxEnergy, maxTime and maxSoC is required')
    session.station.limits_to_send[body.get('transactionId')] = limit
    return {'status': 'Accepted'}


async def _trigger_update_dynamic_schedule(station_id, body):
    """update-dynamic-schedule: from now on the CSMS updates a Dynamic charging profile of the
    station every `interval` seconds with an UpdateDynamicScheduleRequest (K28, Q04), until
    the profile is cleared."""
    session = _session(station_id)
    try:
        profile_id, interval = int(body['chargingProfileId']), float(body['interval'])
        update = body['scheduleUpdate']
    except (KeyError, TypeError, ValueError):
        raise TriggerError(400, 'chargingProfileId, interval and scheduleUpdate are required')
    if profile_id not in session.station.charging_profiles:
        raise TriggerError(409, f'The station has no charging profile {profile_id}')

    async def push():
        while profile_id in session.station.charging_profiles:
            await asyncio.sleep(interval)
            if profile_id not in session.station.charging_profiles:
                break
            await session.call('UpdateDynamicSchedule',
                               {'chargingProfileId': profile_id, 'scheduleUpdate': update})

    session.later(push())
    return {'status': 'Accepted'}


async def _trigger_clear_variable_monitoring(station_id, body):
    """clear-variable-monitoring: ClearVariableMonitoringRequest(s) for the monitor ids, split
    by ItemsPerMessageClearVariableMonitoring (N06.FR.04)."""
    session = _session(station_id)
    return await _batched(
        session, 'ClearVariableMonitoring', 'id', 'clearMonitoringResult', body.get('id', []),
        session.station.limit('MonitoringCtrlr', 'ItemsPerMessage', 'ClearVariableMonitoring'))


async def _trigger_get_log(station_id, body):
    """get-log: a GetLogRequest for a log that the station uploads to the log server of the
    CSMS, over HTTP or HTTPS: the CSMS gives the location, with the userinfo for HTTP Basic
    Authentication (N01)."""
    session = _session(station_id)
    scheme = body.get('scheme', 'http')
    if scheme not in ('http', 'https'):
        raise TriggerError(400, 'scheme is http or https')
    request_id = int(body.get('requestId', 1))
    port = LOG_HTTPS_PORT if scheme == 'https' else TRIGGER_PORT
    location = (f"{scheme}://{LOG_UPLOAD_USER}:{LOG_UPLOAD_PASSWORD}@localhost:{port}"
                f"/logs/{station_id}-{request_id}.log")
    return await _relay(session, 'GetLog', {
        'logType': body.get('logType', 'DiagnosticsLog'),
        'requestId': request_id,
        'log': {'remoteLocation': location},
    })


def _store_log(path, authorization):
    """The log server of the CSMS: an upload needs HTTP Basic Authentication."""
    import base64
    expected = base64.b64encode(f"{LOG_UPLOAD_USER}:{LOG_UPLOAD_PASSWORD}".encode()).decode()
    if authorization != f"Basic {expected}":
        raise TriggerError(401, 'Unauthorized')
    return {'status': 'stored', 'path': path}


async def _trigger_provide_charging_profiles(station_id, body):
    """provide-charging-profiles: turn on or off that the CSMS provides a charging profile
    for the charging needs of an EV at this station (K15 - K20)."""
    session = _session(station_id)
    if not isinstance(body.get('enabled'), bool):
        raise TriggerError(400, 'enabled (true or false) is required')
    session.station.provide_charging_profiles = body['enabled']
    return {'status': 'Accepted'}


async def _trigger_driver_tariff(body):
    """driver-tariff: configure the driver-specific tariff that the CSMS provides for an
    idToken (I08), or remove it when the tariff is null."""
    try:
        token = body['idToken']['idToken'].upper()
    except (KeyError, TypeError, AttributeError):
        raise TriggerError(400, 'idToken.idToken is required')
    tariff = body.get('tariff')
    if tariff is None:
        DRIVER_TARIFFS.pop(token, None)
        return {'status': 'Accepted'}
    # I08.FR.09: a driver-specific tariff has no validFrom
    tariff = {field: value for field, value in tariff.items() if field != 'validFrom'}
    try:
        validate('AuthorizeResponse', {'idTokenInfo': {'status': 'Accepted'}, 'tariff': tariff})
    except SchemaViolation as violation:
        raise TriggerError(400, str(violation))
    DRIVER_TARIFFS[token] = tariff
    return {'status': 'Accepted'}


async def _remote_start_for_payment(session, psp_ref, evse_id, limit, additional_info=None):
    """C24.FR.01, C25.FR.23: start a transaction remotely for an authorized ad hoc payment,
    with the PspRef as idToken of type DirectPayment."""
    session.station.payments[psp_ref] = limit
    id_token = {'idToken': psp_ref, 'type': 'DirectPayment'}
    if additional_info:
        id_token['additionalInfo'] = additional_info
    request = {'remoteStartId': session.station.next_remote_start_id(), 'idToken': id_token}
    if evse_id is not None:
        request['evseId'] = evse_id
    return await _relay(session, 'RequestStartTransaction', request)


async def _trigger_kiosk_payment_authorized(station_id, body):
    """kiosk-payment-authorized: a stand-alone payment terminal tells the CSMS that a payment
    is authorized for this station (C24)."""
    session = _session(station_id)
    try:
        psp_ref, amount = body['pspRef'], float(body['authorizationAmount'])
    except (KeyError, TypeError, ValueError):
        raise TriggerError(400, 'pspRef and authorizationAmount are required')
    additional_info = None
    if body.get('cardLast4Digits'):
        additional_info = [{'additionalIdToken': str(body['cardLast4Digits']),
                            'type': 'CardLast4Digits'}]
    # C24.FR.02: the transaction may cost up to the authorized amount
    return await _remote_start_for_payment(
        session, psp_ref, body.get('evseId'), {'max_cost': amount}, additional_info)


async def _trigger_qr_code_payment(body):
    """qr-code-payment: an EV Driver visited the payment web page with the URL of a QR code
    and paid at the PSP (C25)."""
    try:
        station_id, evse_id, limit = decode_qr_code_url(body.get('qrUrl', ''))
    except ValueError as invalid:
        # C25.FR.08: no payment and no transaction for a URL that is not valid
        logging.warning(f"QR code URL {body.get('qrUrl')!r}: {invalid}")
        return {'status': 'Rejected', 'reason': str(invalid)}
    # The PSP authorizes the payment, and gives its reference.
    psp_ref = f"PSP-{uuid.uuid4()}"
    return await _remote_start_for_payment(_session(station_id), psp_ref, evse_id, limit)


_STATION_ENDPOINTS = {
    'trigger-message': _trigger_message,
    'set-network-configuration': _trigger_set_network_configuration,
    'kiosk-payment-authorized': _trigger_kiosk_payment_authorized,
    'set-transaction-limit': _trigger_set_transaction_limit,
    'provide-charging-profiles': _trigger_provide_charging_profiles,
    'clear-variable-monitoring': _trigger_clear_variable_monitoring,
    'update-dynamic-schedule': _trigger_update_dynamic_schedule,
    'get-log': _trigger_get_log,
    'update-basic-auth-password': _trigger_update_basic_auth_password,
    'set-security-profile': _trigger_set_security_profile,
    'set-pending-boot': _trigger_set_pending_boot,
    'get-variables': _trigger_get_variables,
    'set-variables': _trigger_set_variables,
}


async def _route_trigger(method, path, body):
    """Route an HTTP trigger request to its handler."""
    if method == 'GET' and path.startswith('/receipts/'):
        # Not part of the trigger API: the receipt of an ad hoc payment (C21.FR.03)
        receipt = RECEIPTS.get(path[len('/receipts/'):])
        if receipt is None:
            raise TriggerError(404, 'Unknown receipt')
        return receipt
    if method != 'POST':
        raise TriggerError(405, 'Method not allowed')

    if path == '/api/octt/set-basic-auth-password':
        return await _trigger_set_basic_auth_password(body)
    if path == '/api/octt/2.1/qr-code-payment':
        return await _trigger_qr_code_payment(body)
    if path == '/api/octt/2.1/driver-tariff':
        return await _trigger_driver_tariff(body)

    prefix = '/api/octt/2.1/'
    if not path.startswith(prefix):
        raise TriggerError(404, f'Unknown path: {path}')
    station_id, _, endpoint = path[len(prefix):].partition('/')
    if not endpoint:
        raise TriggerError(400, 'Missing endpoint in path')

    if endpoint.startswith('call/'):
        return await _trigger_call(station_id, endpoint[len('call/'):], body)
    handler = _STATION_ENDPOINTS.get(endpoint)
    if handler is None:
        raise TriggerError(404, f'Unknown endpoint: {endpoint}')
    return await handler(station_id, body)


_HTTP_REASONS = {200: 'OK', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found',
                 405: 'Method Not Allowed',
                 409: 'Conflict', 500: 'Internal Server Error'}


async def _handle_trigger_http(reader, writer):
    """Handle a single HTTP request on the trigger API port."""
    status, answer = 500, {'error': 'Internal error'}
    try:
        request_line = await asyncio.wait_for(reader.readline(), timeout=5)
        parts = request_line.decode().strip().split(' ')
        if len(parts) < 2:
            raise TriggerError(400, 'Bad request')
        method, path = parts[0], parts[1]

        content_length, authorization = 0, None
        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=5)
            if line in (b'\r\n', b'\n', b''):
                break
            if line.lower().startswith(b'content-length:'):
                content_length = int(line.split(b':')[1].strip())
            elif line.lower().startswith(b'authorization:'):
                authorization = line.split(b':', 1)[1].strip().decode()

        raw = b''
        if content_length > 0:
            raw = await asyncio.wait_for(reader.readexactly(content_length), timeout=5)
        if method == 'POST' and path.startswith('/logs/'):
            # Not part of the trigger API: the upload of a log file by a station (N01)
            logging.info(f"Log upload: {path} ({content_length} bytes)")
            status, answer = 200, _store_log(path, authorization)
            return

        body = json.loads(raw.decode()) if raw else {}

        logging.info(f"Trigger: {method} {path} {json.dumps(body)}")
        status, answer = 200, await _route_trigger(method, path, body)
    except TriggerError as error:
        logging.warning(f"Trigger: {error.status} {error.message}")
        status, answer = error.status, {'error': error.message}
    except Exception as error:
        logging.exception("Trigger API error")
        status, answer = 500, {'error': repr(error)}
    finally:
        try:
            data = json.dumps(answer).encode()
            writer.write((
                f"HTTP/1.1 {status} {_HTTP_REASONS.get(status, 'Error')}\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(data)}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            ).encode() + data)
            await writer.drain()
            writer.close()
        except Exception:
            pass


# ─── Main ────────────────────────────────────────────────────────────────────

async def main():
    wss_server = await websockets.serve(
        on_connect,
        '0.0.0.0',
        WSS_PORT,
        create_protocol=StationProtocol,
        subprotocols=[SUBPROTOCOL],
        ssl=create_server_ssl_context(),
    )
    logging.info(f"WSS server started on port {WSS_PORT}")

    trigger_server = await asyncio.start_server(_handle_trigger_http, '0.0.0.0', TRIGGER_PORT)
    logging.info(f"Trigger API server started on port {TRIGGER_PORT}")
    # The log server of the CSMS over HTTPS (TC_N_103); over HTTP it is on the trigger port.
    await asyncio.start_server(_handle_trigger_http, '0.0.0.0', LOG_HTTPS_PORT,
                               ssl=create_server_ssl_context())

    logging.info("------------------------------------------------------------")
    logging.info("CSMS 2.1 simulator started.")
    logging.info("This implementation should be used only for testing the tzi-OCTT suite.")
    logging.info("It is not intended for production or general-purpose use.")
    logging.info("")

    await asyncio.gather(wss_server.wait_closed(), trigger_server.serve_forever())


if __name__ == '__main__':
    asyncio.run(main())
