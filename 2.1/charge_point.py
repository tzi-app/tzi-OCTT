"""Mock Charging Station for the OCPP 2.1 tests: the Test System's side of every scenario.

How a test uses it:

    cp = TziChargePoint21(station_id, connection)
    start_task = asyncio.create_task(cp.start())

    # The station sends a request and gets the response of the CSMS.
    boot_response = await cp.send_boot_notification()
    response = await cp.call(call.Heartbeat())

    # A Manual Action makes the CSMS send a request. The station answers it, and the test gets
    # the request to validate. set_response() changes the station's answer, which is otherwise
    # the positive one (Accepted, Unlocked, ...).
    cp.set_response('Reset', status='Scheduled')
    request = await cp.wait_for_request(
        'Reset', manual_action=send_call(station_id, 'Reset', {'type': 'OnIdle'}))
    assert request.type == 'OnIdle'
    assert request.evse_id is None          # "evseId must be omitted"

Every message is checked against its OCPP 2.1 JSON schema:
- A request of the CSMS that does not match gets a CALLERROR, and wait_for_request() fails
  with the reason.
- A response of the CSMS that does not match makes call() raise SchemaViolation.
- A request or response of the station itself that does not match is a fault in the test, and
  raises as well. A test that sends an invalid message on purpose passes
  skip_schema_validation=True.

Field names are snake_case in Python and come from the schemas on the wire; ocpp_messages.py
explains the conversion.
"""

import asyncio
import collections
import dataclasses
import json
import logging
import os
import sys
import uuid

import websockets
from ocpp import exceptions as ocpp_exceptions
from ocpp.v21 import call, call_result
from websockets.exceptions import ConnectionClosed

from ocpp_messages import (
    ACTIONS,
    CALL,
    CALL_ERROR,
    CALL_RESULT,
    CALL_RESULT_ERROR,
    MESSAGE_TYPE_NAMES,
    SEND,
    SUBPROTOCOL,
    SchemaViolation,
    canonical,
    from_ocpp,
    to_ocpp,
    utc_now_iso,
    validate,
)
from utils import build_default_ssl_context

ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))

# How long a test waits, in seconds, to see that the CSMS does not send a request.
NO_ACTION_WAIT = int(os.environ.get('CSMS_NO_ACTION_WAIT', '5'))

# The simulated station has CONFIGURED_NUMBER_OF_EVSES EVSEs, numbered from 1, and each has
# the one connector CONFIGURED_CONNECTOR_ID.
CONFIGURED_NUMBER_OF_EVSES = int(os.environ.get('CONFIGURED_NUMBER_OF_EVSES', '1'))
CONFIGURED_CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))

_LOG_MESSAGES = '--log-messages' in sys.argv

# Dedicated logger for OCPP message tracing. It writes directly to /dev/tty, so pytest's
# fd-level capture never swallows the messages.
if _LOG_MESSAGES:
    _tty = open('/dev/tty', 'w')
    _msg_logger = logging.getLogger('ocpp.messages')
    _msg_logger.propagate = False
    _msg_handler = logging.StreamHandler(_tty)
    _msg_handler.setFormatter(logging.Formatter('%(message)s'))
    _msg_logger.addHandler(_msg_handler)
    _msg_logger.setLevel(logging.DEBUG)


class MessageTypeNotSupportedError(ocpp_exceptions.OCPPError):
    code = 'MessageTypeNotSupported'
    default_description = 'A message with a Message Type Number that is not supported'


class RpcFrameworkError(ocpp_exceptions.OCPPError):
    code = 'RpcFrameworkError'
    default_description = 'Content of the call is not a valid RPC Request'


def _error_classes():
    classes = {}
    for error_class in ocpp_exceptions.OCPPError.__subclasses__():
        classes.setdefault(error_class.code, error_class)
    return classes


_ERROR_CLASS_BY_CODE = _error_classes()


class ManualActionFailed(AssertionError):
    """The trigger API call of a Manual Action failed before the CSMS sent its request."""


@dataclasses.dataclass
class CallErrorResponse:
    """A station answer for set_response(): the station answers with a CALLERROR."""
    error_code: str
    error_description: str = ''
    error_details: dict = dataclasses.field(default_factory=dict)


# A station answer for set_response(): the station does not answer the request at all.
NO_RESPONSE = object()


@dataclasses.dataclass
class ReceivedRequest:
    """A request of the CSMS, and the station's answer to it."""
    action: str
    unique_id: str
    payload: object          # snake_case Payload
    raw: dict                # the payload as received
    response: object = None  # the CALLRESULT payload that was sent; None for a CALLERROR


# ─── The station's default answers ───────────────────────────────────────────

def _status(status):
    return lambda cp, request: {'status': status}


def _empty(cp, request):
    return {}


def _set_variables(cp, request):
    return {'set_variable_result': [
        {
            'attribute_status': cp.set_variable_status,
            'attribute_type': item.attribute_type,
            'component': item.component,
            'variable': item.variable,
        }
        for item in request.set_variable_data
    ]}


def _get_variables(cp, request):
    """The values come from cp.variables, whose keys are 'Component.Variable', or
    'Component.Variable[Instance]' for a variable instance."""
    results = []
    for item in request.get_variable_data:
        key = f"{item.component.name}.{item.variable.name}"
        if item.variable.instance is not None:
            key += f"[{item.variable.instance}]"
        result = {
            'attribute_type': item.attribute_type,
            'component': item.component,
            'variable': item.variable,
        }
        if key in cp.variables:
            result['attribute_status'] = 'Accepted'
            result['attribute_value'] = str(cp.variables[key])
        else:
            result['attribute_status'] = 'UnknownVariable'
        results.append(result)
    return {'get_variable_result': results}


def _set_variable_monitoring(cp, request):
    results = []
    for item in request.set_monitoring_data:
        monitor_id = item.id
        if monitor_id is None:
            cp._last_monitor_id += 1
            monitor_id = cp._last_monitor_id
        results.append({
            'id': monitor_id,
            'status': 'Accepted',
            'type': item.type,
            'severity': item.severity,
            'component': item.component,
            'variable': item.variable,
        })
    return {'set_monitoring_result': results}


def _clear_variable_monitoring(cp, request):
    return {'clear_monitoring_result': [
        {'status': 'Accepted', 'id': monitor_id} for monitor_id in request.id
    ]}


def _clear_tariffs(cp, request):
    if request.tariff_ids:
        return {'clear_tariffs_result': [
            {'status': 'Accepted', 'tariff_id': tariff_id} for tariff_id in request.tariff_ids
        ]}
    return {'clear_tariffs_result': [{'status': 'Accepted'}]}


_DEFAULT_RESPONSES = {
    'AdjustPeriodicEventStream': _status('Accepted'),
    'AFRRSignal': _status('Accepted'),
    'CancelReservation': _status('Accepted'),
    'CertificateSigned': _status('Accepted'),
    'ChangeAvailability': _status('Accepted'),
    'ChangeTransactionTariff': _status('Accepted'),
    'ClearCache': _status('Accepted'),
    'ClearChargingProfile': _status('Accepted'),
    'ClearDERControl': _status('Accepted'),
    'ClearDisplayMessage': _status('Accepted'),
    'ClearTariffs': _clear_tariffs,
    'ClearVariableMonitoring': _clear_variable_monitoring,
    'CostUpdated': _empty,
    'CustomerInformation': _status('Accepted'),
    'DataTransfer': _status('UnknownVendorId'),
    'DeleteCertificate': _status('Accepted'),
    'GetBaseReport': _status('Accepted'),
    'GetChargingProfiles': _status('Accepted'),
    'GetCompositeSchedule': _status('Accepted'),
    'GetDERControl': _status('Accepted'),
    'GetDisplayMessages': _status('Accepted'),
    'GetInstalledCertificateIds': _status('Accepted'),
    'GetLocalListVersion': lambda cp, request: {'version_number': cp.local_list_version},
    'GetLog': _status('Accepted'),
    'GetMonitoringReport': _status('Accepted'),
    'GetPeriodicEventStream': _empty,
    'GetReport': _status('Accepted'),
    'GetTariffs': _status('NoTariff'),
    'GetTransactionStatus': lambda cp, request: {'messages_in_queue': False},
    'GetVariables': _get_variables,
    'InstallCertificate': _status('Accepted'),
    'NotifyAllowedEnergyTransfer': _status('Accepted'),
    'NotifyWebPaymentStarted': _empty,
    'PublishFirmware': _status('Accepted'),
    'RequestBatterySwap': _status('Accepted'),
    'RequestStartTransaction': _status('Accepted'),
    'RequestStopTransaction': _status('Accepted'),
    'ReserveNow': _status('Accepted'),
    'Reset': _status('Accepted'),
    'SendLocalList': _status('Accepted'),
    'SetChargingProfile': _status('Accepted'),
    'SetDefaultTariff': _status('Accepted'),
    'SetDERControl': _status('Accepted'),
    'SetDisplayMessage': _status('Accepted'),
    'SetMonitoringBase': _status('Accepted'),
    'SetMonitoringLevel': _status('Accepted'),
    'SetNetworkProfile': _status('Accepted'),
    'SetVariableMonitoring': _set_variable_monitoring,
    'SetVariables': _set_variables,
    'TriggerMessage': _status('Accepted'),
    'UnlockConnector': _status('Unlocked'),
    'UnpublishFirmware': _status('Unpublished'),
    'UpdateDynamicSchedule': _status('Accepted'),
    'UpdateFirmware': _status('Accepted'),
    'UsePriorityCharging': _status('Accepted'),
}


class ChargingSession:
    """What the reusable states know about the charging session on one EVSE: the state of the
    EV driver, the EV and the transaction."""

    def __init__(self):
        self.state = None            # the name of the reusable state the session is in
        self.authorized = False      # an EV driver is authorized for the transaction
        self.ev_connected = False    # "EVConnected is true"
        self.transaction_id = None   # the ongoing transaction
        self.id_token = None         # the idToken that authorized it
        self.evse_id = None          # the EVSE and connector of the session
        self.connector_id = None
        self._seq_no = -1

    def start_transaction(self):
        """A new transaction starts: it gets its id, and its seqNo starts at 0 (E: Sequence
        Number Generation). Returns the transaction id."""
        self.transaction_id = str(uuid.uuid4())
        self._seq_no = -1
        return self.transaction_id

    def next_seq_no(self):
        """The seqNo of the next TransactionEventRequest of this session."""
        self._seq_no += 1
        return self._seq_no


async def connect_to_csms(station_id, headers=None, ssl_context=None, subprotocols=(SUBPROTOCOL,)):
    """Open the station's WebSocket connection to the CSMS (CSMS_ADDRESS).

    Without ssl_context, a wss:// connection verifies the CSMS against TLS_CA_CERT. Raises
    what websockets.connect() raises, for example InvalidStatusCode when the CSMS refuses the
    HTTP upgrade.
    """
    uri = f"{os.environ['CSMS_ADDRESS']}/{station_id}"
    if ssl_context is None and uri.startswith('wss://'):
        ssl_context = build_default_ssl_context()
    connection = await websockets.connect(
        uri=uri,
        subprotocols=list(subprotocols) if subprotocols else None,
        extra_headers=headers,
        ssl=ssl_context,
    )
    # Some delay is required by some CSMS prior to being able to handle data sent
    await asyncio.sleep(0.5)
    return connection


class TziChargePoint21:
    """The simulated Charging Station of the Test System, speaking OCPP 2.1."""

    def __init__(self, id, connection, response_timeout=30):
        self.id = id
        self._connection = connection
        self._response_timeout = response_timeout
        self._call_lock = asyncio.Lock()
        self._pending_calls = {}
        self._last_monitor_id = 0

        # The station's answers that a test has set with set_response()
        self._responses = {}

        # Requests of the CSMS
        self.received_requests = []      # every request that was answered, oldest first
        self._unconsumed = collections.defaultdict(collections.deque)
        self._rejected = collections.defaultdict(list)
        self._activity = asyncio.Event()
        self.sent_call_errors = []       # (action, unique_id, error_code, error_description)
        self.sent_requests = []          # every request of the station: (action, payload as sent)
        self.received_call_result_errors = []
        self.received_unconfirmed = []   # SEND messages of the CSMS: (action, payload)
        self.unexpected_responses = []   # CALLRESULT / CALLERROR messages that answer no request
        self._failure = None
        self.connection_closed = asyncio.Event()

        # The charging session of the scenario. The reusable states (reusable_states/) read
        # and update it. A test with transactions on several EVSEs makes a ChargingSession
        # per EVSE, and passes it to the reusable states.
        self.session = ChargingSession()

        # Station data that the default answers use
        self.variables = {}              # GetVariables: {'Component.Variable': value}
        self.set_variable_status = 'Accepted'   # SetVariables: the status of every variable
        self.local_list_version = 1      # GetLocalListVersion

    # ─── Connection ──────────────────────────────────────────────────────────

    async def start(self):
        """Receive and handle messages until the connection closes."""
        try:
            while True:
                try:
                    message = await self._connection.recv()
                except ConnectionClosed:
                    return
                await self.route_message(message)
        except asyncio.CancelledError:
            connection = getattr(self, "_connection", None)
            if connection is not None:
                try:
                    await connection.close(reason="Normal closure")
                except Exception:
                    # Ignore close-time errors while handling cancellation.
                    pass
            raise
        finally:
            self.connection_closed.set()
            self._activity.set()
            for pending in self._pending_calls.values():
                if not pending.done():
                    pending.set_exception(ConnectionError('The connection to the CSMS closed'))

    async def disconnect(self):
        """Close the WebSocket connection: the Charging Station is offline from here on."""
        await self._connection.close()
        await asyncio.wait_for(self.connection_closed.wait(), timeout=5)

    def use_connection(self, connection):
        """Go on with a new WebSocket connection, after the Charging Station was offline.

        It is the same Charging Station: its charging session, its variables and the answers
        that the test has set are kept. Returns the task that handles the messages of the
        connection, as the task of start() did for the first one.
        """
        self._connection = connection
        self.connection_closed = asyncio.Event()
        return asyncio.create_task(self.start())

    def _fail(self, error):
        """Remember a fault in the message handling, so that the test fails with it."""
        logging.error(f"{self.id}: {error}")
        if self._failure is None:
            self._failure = error
        self._activity.set()

    def _raise_failure(self):
        if self._failure is not None:
            raise self._failure

    @staticmethod
    def _format_ocpp_message(direction, message):
        """Format an OCPP message for logging."""
        msg_type_id = message[0]
        msg_type = MESSAGE_TYPE_NAMES.get(msg_type_id, f'UNKNOWN({msg_type_id})')
        unique_id = message[1] if len(message) > 1 else None

        if msg_type_id in (CALL, SEND):
            payload = message[3] if len(message) > 3 else {}
            header = f"{direction} [{msg_type}] {message[2]} (id={unique_id})"
        elif msg_type_id == CALL_RESULT:
            payload = message[2] if len(message) > 2 else {}
            header = f"{direction} [{msg_type}] (id={unique_id})"
        elif msg_type_id in (CALL_ERROR, CALL_RESULT_ERROR):
            payload = message[4] if len(message) > 4 else {}
            header = f"{direction} [{msg_type}] {message[2]}: {message[3]} (id={unique_id})"
        else:
            header = f"{direction} [{msg_type}] (id={unique_id})"
            payload = message[2:]

        return f"{header}\n{json.dumps(payload, indent=2)}"

    async def _send(self, message):
        if _LOG_MESSAGES:
            _msg_logger.info(self._format_ocpp_message("\nCP  >>>", message))
        await self._connection.send(json.dumps(message, separators=(',', ':')))

    async def route_message(self, raw_msg):
        try:
            message = json.loads(raw_msg)
            if not isinstance(message, list) or len(message) < 3:
                raise ValueError('an OCPP-J message is a JSON array of at least 3 elements')
        except (TypeError, ValueError) as error:
            self._fail(AssertionError(
                f"The CSMS sent a message that is not valid OCPP-J ({error}): {raw_msg!r}"))
            return

        if _LOG_MESSAGES:
            _msg_logger.info(self._format_ocpp_message("\nCSMS >>>", message))

        message_type = message[0]
        if message_type == CALL:
            if len(message) != 4 or not isinstance(message[3], dict):
                self._fail(AssertionError(f"The CSMS sent a malformed CALL: {raw_msg!r}"))
                return
            await self._handle_call(message[1], message[2], message[3])
        elif message_type in (CALL_RESULT, CALL_ERROR):
            pending = self._pending_calls.get(message[1])
            if pending is not None and not pending.done():
                pending.set_result(message)
            else:
                self.unexpected_responses.append(message)
                logging.warning(f"{self.id}: response to an unknown request: {raw_msg!r}")
        elif message_type == CALL_RESULT_ERROR:
            self.received_call_result_errors.append(message)
            logging.error(f"{self.id}: the CSMS could not process a response: {raw_msg!r}")
        elif message_type == SEND:
            self.received_unconfirmed.append((message[2], message[3] if len(message) > 3 else {}))
        # Any other message type: the payload is ignored (OCPP-J 2.1, 4.1.3)

    # ─── Requests of the CSMS ────────────────────────────────────────────────

    def set_response(self, action, response=None, **fields):
        """Set how the station answers <action> requests of the CSMS from now on.

            cp.set_response('Reset', status='Rejected')
            cp.set_response('GetLocalListVersion', version_number=4)
            cp.set_response('GetVariables', lambda request: {...})     # built per request
            cp.set_response('Reset', CallErrorResponse('NotImplemented'))
            cp.set_response('Reset', NO_RESPONSE)

        The answer is snake_case data: keyword arguments, a dict, or a dataclass of
        ocpp.v21.call_result. A function gets the request (a Payload) and returns the answer.
        """
        assert action in _DEFAULT_RESPONSES, f"{action} is not a request that a CSMS sends"
        assert response is None or not fields, "pass either a response or its fields"
        self._responses[action] = fields if response is None else response

    def reset_response(self, action):
        """Answer <action> requests with the station's default answer again."""
        self._responses.pop(action, None)

    def _answer(self, action, request):
        if action in self._responses:
            answer = self._responses[action]
            if callable(answer):
                answer = answer(request)
            return answer
        return _DEFAULT_RESPONSES[action](self, request)

    async def _send_call_error(self, action, unique_id, code, description, details=None):
        self.sent_call_errors.append((action, unique_id, code, description))
        await self._send([CALL_ERROR, unique_id, code, description[:255], details or {}])

    async def _handle_call(self, unique_id, action, raw_payload):
        if action not in ACTIONS:
            await self._send_call_error(
                action, unique_id, 'NotImplemented', f'{action} is not an OCPP 2.1 action')
            self._rejected[action].append(f"{action} is not an OCPP 2.1 action")
            self._activity.set()
            return
        if action not in _DEFAULT_RESPONSES:
            await self._send_call_error(
                action, unique_id, 'NotSupported',
                f'{action}Request is a request of the Charging Station, not of the CSMS')
            self._rejected[action].append(f"a Charging Station does not handle {action}Request")
            self._activity.set()
            return

        try:
            validate(f'{action}Request', raw_payload)
        except SchemaViolation as violation:
            await self._send_call_error(
                action, unique_id, violation.error_code, '; '.join(violation.problems))
            self._rejected[action].append(str(violation))
            self._activity.set()
            return

        request = from_ocpp(f'{action}Request', raw_payload)
        received = ReceivedRequest(action, unique_id, request, raw_payload)

        try:
            answer = self._answer(action, request)
            if answer is NO_RESPONSE:
                pass
            elif isinstance(answer, CallErrorResponse):
                await self._send_call_error(
                    action, unique_id, answer.error_code, answer.error_description,
                    answer.error_details)
            else:
                response = to_ocpp(f'{action}Response', answer)
                validate(f'{action}Response', response)
                received.response = response
                await self._send([CALL_RESULT, unique_id, response])
        except Exception as error:
            # The station's own answer is wrong: a fault in the test, not in the CSMS.
            await self._send_call_error(action, unique_id, 'InternalError', 'Test System fault')
            self._fail(AssertionError(
                f"The Test System could not answer {action}Request: {error!r}"))
            return

        # The request counts as received once its answer is on its way, so that a test that
        # waits for it sends its next message after the answer.
        self.received_requests.append(received)
        self._unconsumed[action].append(received)
        self._activity.set()

    async def wait_for_request(self, action, manual_action=None, timeout=ACTION_TIMEOUT):
        """The next <action> request of the CSMS, once the station has answered it.

        manual_action is the trigger API call that makes the CSMS send the request: the Manual
        Action of the test case. Requests that arrived before it are not the one it causes, so
        they are dropped first. The call then has to return, which the CSMS does after it got
        the station's answer.

        Without manual_action, this returns the oldest <action> request that no earlier call
        returned, and waits for one if there is none.

        Returns the request as a snake_case Payload.
        """
        assert action in _DEFAULT_RESPONSES, f"{action} is not a request that a CSMS sends"
        self._raise_failure()
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        trigger = None
        if manual_action is not None:
            self._unconsumed[action].clear()
            self._rejected[action].clear()
            trigger = asyncio.ensure_future(manual_action)

        try:
            while True:
                self._activity.clear()
                if self._unconsumed[action]:
                    received = self._unconsumed[action].popleft()
                    break
                if self._rejected[action]:
                    raise AssertionError(
                        f"The CSMS sent a {action}Request that the Charging Station answered "
                        f"with a CALLERROR: {self._rejected[action][0]}")
                self._raise_failure()
                if trigger is not None and trigger.done() and trigger.exception() is not None:
                    raise ManualActionFailed(
                        f"The trigger API call for {action} failed: {trigger.exception()!r}"
                    ) from trigger.exception()
                if self.connection_closed.is_set():
                    raise ConnectionError(
                        f"The connection closed while waiting for {action}Request")
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise asyncio.TimeoutError(
                        f"The CSMS did not send {action}Request within {timeout} s")

                waiting = {asyncio.ensure_future(self._activity.wait())}
                if trigger is not None and not trigger.done():
                    waiting.add(trigger)
                await asyncio.wait(waiting, timeout=remaining, return_when=asyncio.FIRST_COMPLETED)
                for task in waiting:
                    if task is not trigger and not task.done():
                        task.cancel()

            if trigger is not None:
                # The CSMS answers the trigger API call once it has the station's answer.
                try:
                    await asyncio.wait_for(asyncio.shield(trigger), max(deadline - loop.time(), 1))
                except asyncio.TimeoutError:
                    raise asyncio.TimeoutError(
                        f"The trigger API call for {action} did not return within {timeout} s, "
                        f"although the Charging Station answered the request") from None
                except Exception as error:
                    # The request arrived, so the Manual Action was performed.
                    logging.warning(f"{self.id}: the trigger API call for {action} failed "
                                    f"after the CSMS sent the request: {error!r}")
            return received.payload
        finally:
            if trigger is not None:
                if not trigger.done():
                    trigger.cancel()
                elif not trigger.cancelled():
                    trigger.exception()

    def forget_requests(self, action):
        """Drop the <action> requests that no wait_for_request() call has returned yet, so
        that the next call returns a request that arrives from now on."""
        self._unconsumed[action].clear()
        self._rejected[action].clear()

    def requests_of(self, action):
        """The <action> requests the station has answered so far, oldest first."""
        return [received.payload for received in self.received_requests
                if received.action == action]

    async def expect_no_request(self, action, during=NO_ACTION_WAIT, manual_action=None):
        """Check that the CSMS sends no <action> request: not during the Manual Action (the
        trigger API call), when there is one, and not in the `during` seconds after it."""
        before = len(self.requests_of(action))
        if manual_action is not None:
            await manual_action
        await asyncio.sleep(during)
        self._raise_failure()
        after = self.requests_of(action)
        assert len(after) == before, \
            f"The CSMS sent a {action}Request, which the scenario does not have: {after[-1]}"

    async def drain_post_boot(self, delay=1.0):
        """Wait for the messages a CSMS sends on its own after accepting a boot, and forget
        them, so that a test only sees the requests of its scenario. The CSMS may send
        SetVariables (tariff configuration), GetBaseReport, ReserveNow (active reservations),
        GetTransactionStatus, etc. after accepting a boot.
        """
        await asyncio.sleep(delay)
        self.received_requests.clear()
        self._unconsumed.clear()
        self._rejected.clear()

    # ─── Requests of the station ─────────────────────────────────────────────

    def next_seq_no(self):
        """The seqNo of the next TransactionEventRequest of the scenario's charging session."""
        return self.session.next_seq_no()

    async def call(self, payload, suppress=False, unique_id=None, skip_schema_validation=False):
        """Send a request and return the response of the CSMS.

        payload is a dataclass of ocpp.v21.call. The response is the matching dataclass of
        ocpp.v21.call_result; its OCPP objects are Payloads (ocpp_messages.py).

        A CALLERROR raises the matching ocpp.exceptions error, or returns None with
        suppress=True. skip_schema_validation=True sends the request as it is and does not
        check the response either.
        """
        action = type(payload).__name__
        request = to_ocpp(f'{action}Request', payload)
        if not skip_schema_validation:
            validate(f'{action}Request', request)
        return await self.call_raw(
            action, request, suppress=suppress, unique_id=unique_id,
            validate_response=not skip_schema_validation)

    async def call_raw(self, action, request, suppress=False, unique_id=None,
                       validate_response=True):
        """Send a request whose payload is given as it goes on the wire (camelCase)."""
        self._raise_failure()
        unique_id = unique_id if unique_id is not None else str(uuid.uuid4())
        pending = asyncio.get_running_loop().create_future()

        async with self._call_lock:
            self._pending_calls[unique_id] = pending
            try:
                await self._send([CALL, unique_id, action, request])
                self.sent_requests.append((action, request))
                message = await asyncio.wait_for(pending, self._response_timeout)
            except asyncio.TimeoutError:
                raise asyncio.TimeoutError(
                    f"The CSMS did not answer {action}Request within {self._response_timeout} s"
                ) from None
            finally:
                self._pending_calls.pop(unique_id, None)

        if message[0] == CALL_ERROR:
            if suppress:
                return None
            error_code = message[2] if len(message) > 2 else 'GenericError'
            error_class = _ERROR_CLASS_BY_CODE.get(error_code, ocpp_exceptions.GenericError)
            raise error_class(
                description=message[3] if len(message) > 3 else None,
                details=message[4] if len(message) > 4 else None,
            )

        response = message[2]
        if validate_response:
            try:
                validate(f'{action}Response', response)
            except SchemaViolation as violation:
                # Generic requirement FR.06: an invalid response is answered with a
                # CALLRESULTERROR. The test fails with the violation.
                await self._send([CALL_RESULT_ERROR, unique_id, violation.error_code,
                                  '; '.join(violation.problems)[:255], {}])
                raise
        return self._response_object(action, response)

    @staticmethod
    def _response_object(action, response):
        result_class = getattr(call_result, action)
        fields = {canonical(field.name): field.name for field in dataclasses.fields(result_class)}
        data = from_ocpp(f'{action}Response', response)
        values = {fields[canonical(key)]: value for key, value in data.items()
                  if canonical(key) in fields}
        try:
            result = result_class(**values)
        except TypeError:
            # Only without schema validation: a required field is missing.
            result = result_class.__new__(result_class)
            for name in fields.values():
                setattr(result, name, values.get(name))
        result.payload = response
        return result

    async def send_unconfirmed(self, action, data, unique_id=None, skip_schema_validation=False):
        """Send a message with the SEND message type: it has no response (OCPP-J 2.1, 4.2.4)."""
        self._raise_failure()
        payload = to_ocpp(action, data)
        if not skip_schema_validation:
            validate(action, payload)
        unique_id = unique_id if unique_id is not None else str(uuid.uuid4())
        await self._send([SEND, unique_id, action, payload])
        return unique_id

    async def send_boot_notification(self, drain=True, reason='PowerUp', serial_number=None,
                                     model='CP Model 1.0', vendor_name='tzi.app'):
        charging_station = {'model': model, 'vendor_name': vendor_name}
        if serial_number is not None:
            charging_station['serial_number'] = serial_number
        response = await self.call(call.BootNotification(
            charging_station=charging_station,
            reason=reason,
        ))
        if drain and response.status == 'Accepted':
            await self.drain_post_boot()
        return response

    async def send_status_notification(self, connector_id, status, evse_id=1):
        return await self.call(call.StatusNotification(
            timestamp=utc_now_iso(),
            connector_id=connector_id,
            evse_id=evse_id,
            connector_status=status,
        ))

    async def send_notify_event(self, data, seq_no=0, tbc=False):
        return await self.call(call.NotifyEvent(
            generated_at=utc_now_iso(), seq_no=seq_no, event_data=data, tbc=tbc))

    async def send_event(self, component, variable, actual_value, trigger='Delta',
                         event_notification_type='HardWiredNotification', **fields):
        """Send a NotifyEventRequest with one event: the value of a variable of a component.

        component and variable are names, or ComponentType / VariableType data. fields are
        other EventDataType fields, such as transaction_id, severity or cleared.
        """
        return await self.send_notify_event([{
            'event_id': self._next_event_id(),
            'timestamp': utc_now_iso(),
            'trigger': trigger,
            'actual_value': actual_value,
            'event_notification_type': event_notification_type,
            'component': {'name': component} if isinstance(component, str) else component,
            'variable': {'name': variable} if isinstance(variable, str) else variable,
            **fields,
        }])

    async def send_connector_status(self, status, evse_id=1, connector_id=1,
                                    status_notification=True):
        """Notify the CSMS about the state of a connector, with both messages a Charging
        Station has for it:
            StatusNotificationRequest - connectorStatus <status>
            NotifyEventRequest - trigger Delta, actualValue <status>, component.name Connector,
                                 variable.name AvailabilityState
        status_notification=False sends the NotifyEventRequest only, for the test cases that
        have no StatusNotificationRequest in this step.
        """
        if status_notification:
            await self.send_status_notification(connector_id, status, evse_id=evse_id)
        await self.send_notify_event([{
            'event_id': self._next_event_id(),
            'timestamp': utc_now_iso(),
            'trigger': 'Delta',
            'actual_value': status,
            'event_notification_type': 'HardWiredNotification',
            'component': {'name': 'Connector', 'evse': {'id': evse_id, 'connector_id': connector_id}},
            'variable': {'name': 'AvailabilityState'},
        }])

    async def send_all_connectors_status(self, status='Available', other_status=None,
                                         status_notification=True):
        """Notify the CSMS about the current state of all connectors.

        other_status: {evse_id: status} for the connectors that are in another state, for
        example {1: 'Occupied'} while an EV is connected to EVSE 1.
        """
        for evse_id in range(1, CONFIGURED_NUMBER_OF_EVSES + 1):
            await self.send_connector_status(
                (other_status or {}).get(evse_id, status), evse_id=evse_id,
                connector_id=CONFIGURED_CONNECTOR_ID, status_notification=status_notification)

    def _next_event_id(self):
        self._event_id = getattr(self, '_event_id', 0) + 1
        return self._event_id

    async def send_authorization_request(self, id_token, token_type, skip_schema_validation=False):
        return await self.call(
            call.Authorize(id_token={'id_token': id_token, 'type': token_type}),
            skip_schema_validation=skip_schema_validation)

    async def send_authorization_request_with_iso15118(self, id_token, token_type,
                                                       iso15118_certificate_hash_data=None,
                                                       certificate=None):
        """Send an AuthorizeRequest with ISO 15118 certificate data.

        Args:
            id_token: The idToken value (eMAID)
            token_type: The idToken type (e.g. eMAID)
            iso15118_certificate_hash_data: List of OCSPRequestDataType for local cert validation
            certificate: PEM-encoded contract certificate chain for central cert validation
        """
        return await self.call(call.Authorize(
            id_token={'id_token': id_token, 'type': token_type},
            iso_15118_certificate_hash_data=iso15118_certificate_hash_data,
            certificate=certificate,
        ))

    async def send_transaction_event_request(self, event):
        return await self.call(event)

    async def send_sign_certificate_request(self, csr, certificate_type=None):
        return await self.call(call.SignCertificate(csr=csr, certificate_type=certificate_type))

    async def send_security_event_notification(self, event_type, timestamp=None, tech_info=None):
        return await self.call(call.SecurityEventNotification(
            type=event_type, timestamp=timestamp or utc_now_iso(), tech_info=tech_info))

    async def send_notify_report(self, request_id, seq_no, report_data, tbc=False):
        return await self.call(call.NotifyReport(
            request_id=request_id,
            generated_at=utc_now_iso(),
            seq_no=seq_no,
            report_data=report_data,
            tbc=tbc,
        ))

    async def send_reservation_status_update(self, reservation_id, reservation_update_status):
        return await self.call(call.ReservationStatusUpdate(
            reservation_id=reservation_id,
            reservation_update_status=reservation_update_status,
        ))

    async def send_meter_values(self, evse_id, sampled_values=None, timestamp=None,
                                skip_schema_validation=False):
        if sampled_values is None:
            sampled_values = [{'value': 0.0, 'context': 'Trigger'}]
        return await self.call(call.MeterValues(
            evse_id=evse_id,
            meter_value=[{
                'timestamp': timestamp or utc_now_iso(),
                'sampled_value': sampled_values,
            }],
        ), skip_schema_validation=skip_schema_validation)

    async def send_log_status_notification_request(self, status='Idle', request_id=None):
        return await self.call(call.LogStatusNotification(status=status, request_id=request_id))

    async def send_firmware_status_notification_request(self, status='Idle', request_id=None):
        return await self.call(call.FirmwareStatusNotification(status=status, request_id=request_id))

    async def send_publish_firmware_status_notification_request(self, status, location=None,
                                                                request_id=None):
        return await self.call(call.PublishFirmwareStatusNotification(
            status=status, location=location, request_id=request_id))

    async def send_data_transfer(self, vendor_id, message_id=None, data=None):
        return await self.call(call.DataTransfer(vendor_id=vendor_id, message_id=message_id, data=data))

    async def send_heartbeat_request(self):
        return await self.call(call.Heartbeat())

    async def send_get_certificate_status_request(self, ocsp_request_data):
        return await self.call(call.GetCertificateStatus(ocsp_request_data=ocsp_request_data))

    async def send_get_15118_ev_certificate_request(self, iso15118_schema_version, action,
                                                    exi_request,
                                                    maximum_contract_certificate_chains=None,
                                                    prioritized_emaids=None):
        return await self.call(call.Get15118EVCertificate(
            iso_15118_schema_version=iso15118_schema_version,
            action=action,
            exi_request=exi_request,
            maximum_contract_certificate_chains=maximum_contract_certificate_chains,
            prioritized_emaids=prioritized_emaids,
        ))

    async def send_notify_monitoring_report(self, request_id, seq_no, monitor=None, tbc=False):
        return await self.call(call.NotifyMonitoringReport(
            request_id=request_id,
            seq_no=seq_no,
            generated_at=utc_now_iso(),
            monitor=monitor,
            tbc=tbc,
        ))

    async def send_notify_customer_information(self, data, seq_no, request_id, tbc=False):
        return await self.call(call.NotifyCustomerInformation(
            data=data,
            seq_no=seq_no,
            generated_at=utc_now_iso(),
            request_id=request_id,
            tbc=tbc,
        ))

    async def send_notify_display_messages(self, request_id, message_info=None, tbc=False):
        return await self.call(call.NotifyDisplayMessages(
            request_id=request_id,
            message_info=message_info,
            tbc=tbc,
        ))
