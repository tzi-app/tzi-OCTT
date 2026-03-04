import asyncio
import dataclasses
import json
from typing import List
import logging
import sys

from ocpp.routing import on
from ocpp.v201 import call, call_result
from ocpp.v201 import ChargePoint
from ocpp.v201.datatypes import (
    EventDataType, StatusInfoType
)
from ocpp.v201.call import TransactionEvent, ClearCache, Authorize
from ocpp.v201.enums import (
    Action, SetVariableStatusEnumType, TriggerMessageStatusEnumType,
    CertificateSignedStatusEnumType, GenericStatusEnumType,
    GetVariableStatusEnumType,
    GenericDeviceModelStatusEnumType, ResetStatusEnumType,
    ClearCacheStatusEnumType as ClearCacheStatusType,
    SendLocalListStatusEnumType,
    RequestStartStopStatusEnumType,
    UnlockStatusEnumType,
    ChangeAvailabilityStatusEnumType,
    ReserveNowStatusEnumType,
    CancelReservationStatusEnumType,
    UpdateFirmwareStatusEnumType,
    UnpublishFirmwareStatusEnumType,
    InstallCertificateStatusEnumType,
    GetInstalledCertificateStatusEnumType,
    DeleteCertificateStatusEnumType,
    SetNetworkProfileStatusEnumType,
    ChargingProfileStatusEnumType,
    ClearChargingProfileStatusEnumType,
    GetChargingProfileStatusEnumType,
    SetMonitoringStatusEnumType,
    ClearMonitoringStatusEnumType,
    LogStatusEnumType,
    CustomerInformationStatusEnumType,
    DisplayMessageStatusEnumType,
    GetDisplayMessagesStatusEnumType,
    ClearMessageStatusEnumType,
)

from utils import now_iso

_MSG_TYPE_NAMES = {2: 'CALL', 3: 'CALL_RESULT', 4: 'CALL_ERROR'}
_LOG_MESSAGES = '--log-messages' in sys.argv

# Dedicated logger for OCPP message tracing — writes directly to /dev/tty
# so pytest's fd-level capture never swallows the messages.
if _LOG_MESSAGES:
    _tty = open('/dev/tty', 'w')
    _msg_logger = logging.getLogger('ocpp.messages')
    _msg_logger.propagate = False
    _msg_handler = logging.StreamHandler(_tty)
    _msg_handler.setFormatter(logging.Formatter('%(message)s'))
    _msg_logger.addHandler(_msg_handler)
    _msg_logger.setLevel(logging.DEBUG)


class AttributeDict(dict):
    """Dict subclass that supports attribute-style access on nested dicts.
    Allows both d['key'] and d.key access patterns.
    """
    def __getattr__(self, key):
        try:
            value = self[key]
            if isinstance(value, dict) and not isinstance(value, AttributeDict):
                return AttributeDict(value)
            return value
        except KeyError:
            raise AttributeError(key)


def _wrap_dicts(obj):
    """Convert plain dict fields in a dataclass response to AttributeDict
    so tests can use both dict-style and attribute-style access."""
    if not dataclasses.is_dataclass(obj) or isinstance(obj, type):
        return obj
    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        if isinstance(value, dict) and not isinstance(value, AttributeDict):
            setattr(obj, field.name, AttributeDict(value))
    return obj


class TziChargePoint(ChargePoint):
    seq_no = 0
    notify_event_sent = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._received_set_variables = asyncio.Event()
        self._received_trigger_message = asyncio.Event()
        self._received_certificate_signed = asyncio.Event()
        self._set_variables_data = None
        self._trigger_message_data = None
        self._certificate_signed_data = None
        self._set_variables_response_status = SetVariableStatusEnumType.accepted
        self._certificate_signed_response_status = CertificateSignedStatusEnumType.accepted
        self._received_get_variables = asyncio.Event()
        self._received_get_base_report = asyncio.Event()
        self._received_get_report = asyncio.Event()
        self._received_reset = asyncio.Event()
        self._get_variables_data = None
        self._get_base_report_data = None
        self._get_report_data = None
        self._reset_data = None
        self._get_variables_values = {}
        self._reset_response_status = ResetStatusEnumType.accepted
        self._get_report_response_status = GenericDeviceModelStatusEnumType.accepted
        self._received_clear_cache = asyncio.Event()
        self._clear_cache_response_status = ClearCacheStatusType.accepted
        self._received_send_local_list = asyncio.Event()
        self._received_get_local_list_version = asyncio.Event()
        self._send_local_list_data = None
        self._send_local_list_response_status = SendLocalListStatusEnumType.accepted
        self._local_list_version = 1
        self._received_request_start_transaction = asyncio.Event()
        self._request_start_transaction_data = None
        self._request_start_transaction_response_status = RequestStartStopStatusEnumType.accepted
        self._request_start_transaction_response_transaction_id = None
        self._received_request_stop_transaction = asyncio.Event()
        self._request_stop_transaction_data = None
        self._request_stop_transaction_response_status = RequestStartStopStatusEnumType.accepted
        self._received_get_transaction_status = asyncio.Event()
        self._get_transaction_status_data = None
        self._get_transaction_status_messages_in_queue = False
        self._get_transaction_status_ongoing_indicator = None
        self._received_unlock_connector = asyncio.Event()
        self._unlock_connector_data = None
        self._unlock_connector_response_status = UnlockStatusEnumType.unlocked
        self._trigger_message_response_status = TriggerMessageStatusEnumType.accepted
        self._trigger_message_evse = None
        self._received_change_availability = asyncio.Event()
        self._change_availability_data = None
        self._change_availability_response_status = ChangeAvailabilityStatusEnumType.accepted
        self._received_reserve_now = asyncio.Event()
        self._reserve_now_data = None
        self._reserve_now_response_status = ReserveNowStatusEnumType.accepted
        self._received_cancel_reservation = asyncio.Event()
        self._cancel_reservation_data = None
        self._cancel_reservation_response_status = CancelReservationStatusEnumType.accepted
        self._received_update_firmware = asyncio.Event()
        self._update_firmware_data = None
        self._update_firmware_response_status = UpdateFirmwareStatusEnumType.accepted
        self._received_publish_firmware = asyncio.Event()
        self._publish_firmware_data = None
        self._publish_firmware_response_status = GenericStatusEnumType.accepted
        self._received_unpublish_firmware = asyncio.Event()
        self._unpublish_firmware_data = None
        self._unpublish_firmware_response_status = UnpublishFirmwareStatusEnumType.unpublished
        self._received_cost_updated = asyncio.Event()
        self._cost_updated_data = None
        self._received_install_certificate = asyncio.Event()
        self._install_certificate_data = None
        self._install_certificate_response_status = InstallCertificateStatusEnumType.accepted
        self._received_get_installed_certificate_ids = asyncio.Event()
        self._get_installed_certificate_ids_data = None
        self._get_installed_certificate_ids_response_status = GetInstalledCertificateStatusEnumType.accepted
        self._get_installed_certificate_ids_response_chain = None
        self._received_delete_certificate = asyncio.Event()
        self._delete_certificate_data = None
        self._delete_certificate_response_status = DeleteCertificateStatusEnumType.accepted
        self._received_set_network_profile = asyncio.Event()
        self._set_network_profile_data = None
        self._set_network_profile_response_status = SetNetworkProfileStatusEnumType.accepted
        self._received_set_charging_profile = asyncio.Event()
        self._set_charging_profile_data = None
        self._set_charging_profile_response_status = ChargingProfileStatusEnumType.accepted
        self._received_clear_charging_profile = asyncio.Event()
        self._clear_charging_profile_data = None
        self._clear_charging_profile_response_status = ClearChargingProfileStatusEnumType.accepted
        self._received_get_charging_profiles = asyncio.Event()
        self._get_charging_profiles_data = None
        self._get_charging_profiles_response_status = GetChargingProfileStatusEnumType.accepted
        self._received_get_composite_schedule = asyncio.Event()
        self._get_composite_schedule_data = None
        self._get_composite_schedule_response_status = GenericStatusEnumType.accepted
        self._get_composite_schedule_response_schedule = None
        self._received_get_monitoring_report = asyncio.Event()
        self._get_monitoring_report_data = None
        self._get_monitoring_report_response_status = GenericDeviceModelStatusEnumType.accepted
        self._received_set_monitoring_base = asyncio.Event()
        self._set_monitoring_base_data = None
        self._set_monitoring_base_response_status = GenericDeviceModelStatusEnumType.accepted
        self._received_set_variable_monitoring = asyncio.Event()
        self._set_variable_monitoring_data = None
        self._set_variable_monitoring_response_results = None
        self._received_set_monitoring_level = asyncio.Event()
        self._set_monitoring_level_data = None
        self._set_monitoring_level_response_status = GenericStatusEnumType.accepted
        self._received_clear_variable_monitoring = asyncio.Event()
        self._clear_variable_monitoring_data = None
        self._clear_variable_monitoring_response_results = None
        self._received_customer_information = asyncio.Event()
        self._customer_information_data = None
        self._customer_information_response_status = CustomerInformationStatusEnumType.accepted
        self._received_get_log = asyncio.Event()
        self._get_log_data = None
        self._get_log_response_status = LogStatusEnumType.accepted
        self._received_set_display_message = asyncio.Event()
        self._set_display_message_data = None
        self._set_display_message_response_status = DisplayMessageStatusEnumType.accepted
        self._received_get_display_messages = asyncio.Event()
        self._get_display_messages_data = None
        self._get_display_messages_response_status = GetDisplayMessagesStatusEnumType.accepted
        self._received_clear_display_message = asyncio.Event()
        self._clear_display_message_data = None
        self._clear_display_message_response_status = ClearMessageStatusEnumType.accepted

    def next_seq_no(self):
        self.seq_no += 1
        return self.seq_no

    def get_notify_event_type(self):
        if self.notify_event_sent:
            return 'Updated'

        self.notify_event_sent = True
        return 'Started'

    async def call(self, payload, suppress=False, unique_id=None, skip_schema_validation=True):
        response = await super().call(
            payload, suppress=suppress, unique_id=unique_id,
            skip_schema_validation=skip_schema_validation,
        )
        return _wrap_dicts(response)

    def _format_ocpp_message(self, direction, raw_msg):
        """Format an OCPP message for logging."""
        try:
            msg = json.loads(raw_msg)
        except (json.JSONDecodeError, TypeError):
            return f"{direction} {raw_msg}"

        msg_type_id = msg[0]
        msg_type = _MSG_TYPE_NAMES.get(msg_type_id, f'UNKNOWN({msg_type_id})')
        unique_id = msg[1]

        if msg_type_id == 2:  # CALL
            action = msg[2]
            payload = msg[3]
            header = f"{direction} [{msg_type}] {action} (id={unique_id})"
        elif msg_type_id == 3:  # CALL_RESULT
            payload = msg[2]
            header = f"{direction} [{msg_type}] (id={unique_id})"
        elif msg_type_id == 4:  # CALL_ERROR
            error_code = msg[2]
            error_desc = msg[3]
            payload = msg[4] if len(msg) > 4 else {}
            header = f"{direction} [{msg_type}] {error_code}: {error_desc} (id={unique_id})"
        else:
            header = f"{direction} [{msg_type}] (id={unique_id})"
            payload = msg[2:]

        formatted_payload = json.dumps(payload, indent=2)
        return f"{header}\n{formatted_payload}"

    async def _send(self, message):
        if _LOG_MESSAGES:
            _msg_logger.info(self._format_ocpp_message("\nCP  >>>", message))
        await self._connection.send(message)

    async def route_message(self, raw_msg):
        if _LOG_MESSAGES:
            _msg_logger.info(self._format_ocpp_message("\nCSMS >>>", raw_msg))
        await super().route_message(raw_msg)

    async def start(self):
        try:
            await super().start()
        except asyncio.CancelledError:
            connection = getattr(self, "_connection", None)
            if connection is not None:
                try:
                    await connection.close(reason="Normal closure")
                except Exception:
                    # Ignore close-time errors while handling cancellation.
                    pass
            raise

    async def drain_post_boot(self, delay=1.0):
        """Wait for CSMS post-boot initialization messages to arrive, then clear
        all event flags and captured data so tests only see their own triggered
        messages.  The CSMS may send SetVariables (tariff config), ReserveNow
        (active reservations), GetTransactionStatus, etc. after accepting a boot.
        """
        await asyncio.sleep(delay)
        for attr in list(vars(self)):
            if attr.startswith('_received_') and isinstance(getattr(self, attr), asyncio.Event):
                getattr(self, attr).clear()
            elif attr.endswith('_data') and attr.startswith('_') and not callable(getattr(self, attr)):
                setattr(self, attr, None)

    async def send_boot_notification(self, drain=True):
        payload = call.BootNotification(
            charging_station={
                'model': 'CP Model 1.0',
                'vendor_name': 'tzi.app'
            },
            reason="PowerUp"
        )
        response = await self.call(payload)
        if drain and hasattr(response, 'status') and response.status == 'Accepted':
            await self.drain_post_boot()
        return response

    async def send_boot_notification_with_serial(self, serial_number, drain=True):
        payload = call.BootNotification(
            charging_station={
                'model': 'CP Model 1.0',
                'vendor_name': 'tzi.app',
                'serial_number': serial_number,
            },
            reason="PowerUp"
        )
        response = await self.call(payload)
        if drain and hasattr(response, 'status') and response.status == 'Accepted':
            await self.drain_post_boot()
        return response

    async def send_status_notification(self, connector_id, status, evse_id=1):
        logging.info(f"Sending StatusNotification for evse {evse_id} connector {connector_id} with status {status}...")

        payload = call.StatusNotification(
            timestamp=now_iso(),
            connector_id=connector_id,
            evse_id=evse_id,
            connector_status=status
        )

        logging.info("Received StatusNotification response.")
        return await self.call(payload)

    async def send_notify_event(self, data: List[EventDataType]):
        payload = call.NotifyEvent(generated_at=now_iso(), seq_no=1231230, event_data=data)
        return await self.call(payload)

    async def send_authorization_request(self, id_token, token_type, skip_schema_validation=False):
        payload = call.Authorize(id_token=dict(id_token=id_token, type=token_type))
        response = await self.call(payload, skip_schema_validation=skip_schema_validation)
        return response

    async def send_authorization_request_with_iso15118(self, id_token, token_type,
                                                        iso15118_certificate_hash_data=None,
                                                        certificate=None):
        """Send an AuthorizeRequest with optional ISO 15118 certificate data.

        Args:
            id_token: The idToken value (eMAID)
            token_type: The idToken type (e.g. eMAID)
            iso15118_certificate_hash_data: List of OCSPRequestDataType for local cert validation
            certificate: PEM-encoded contract certificate for central cert validation
        """
        from ocpp.v201.datatypes import IdTokenType
        payload = Authorize(
            id_token=IdTokenType(id_token=id_token, type=token_type),
            iso15118_certificate_hash_data=iso15118_certificate_hash_data,
            certificate=certificate,
        )
        response = await self.call(payload)
        return response

    async def send_transaction_event_request(self, event: TransactionEvent):
        response = await self.call(event)
        return response

    async def send_clear_cache_request(self, req: ClearCache) -> StatusInfoType:
        response = await self.call(req)
        return response

    async def send_sign_certificate_request(self, csr, certificate_type=None):
        payload = call.SignCertificate(csr=csr, certificate_type=certificate_type)
        response = await self.call(payload)
        return response

    async def send_security_event_notification(self, event_type, timestamp):
        payload = call.SecurityEventNotification(type=event_type, timestamp=timestamp)
        response = await self.call(payload)
        return response

    async def send_boot_notification_with_reason(self, reason, drain=True):
        payload = call.BootNotification(
            charging_station={
                'model': 'CP Model 1.0',
                'vendor_name': 'tzi.app'
            },
            reason=reason
        )
        response = await self.call(payload)
        if drain and hasattr(response, 'status') and response.status == 'Accepted':
            await self.drain_post_boot()
        return response

    async def send_notify_report(self, request_id, seq_no, report_data, tbc=False):
        payload = call.NotifyReport(
            request_id=request_id,
            generated_at=now_iso(),
            seq_no=seq_no,
            report_data=report_data,
            tbc=tbc,
        )
        response = await self.call(payload)
        return response

    @on(Action.set_variables)
    async def on_set_variables(self, set_variable_data, **kwargs):
        logging.info(f"Received SetVariablesRequest: {set_variable_data}")
        self._set_variables_data = set_variable_data
        self._received_set_variables.set()

        results = []
        for item in set_variable_data:
            component = item.get('component', item) if isinstance(item, dict) else item
            variable = item.get('variable', item) if isinstance(item, dict) else item
            results.append({
                'attribute_status': self._set_variables_response_status,
                'component': component,
                'variable': variable,
            })

        return call_result.SetVariables(set_variable_result=results)

    @on(Action.trigger_message)
    async def on_trigger_message(self, requested_message, evse=None, **kwargs):
        logging.info(f"Received TriggerMessageRequest: {requested_message}, evse={evse}")
        self._trigger_message_data = requested_message
        self._trigger_message_evse = evse
        self._received_trigger_message.set()
        return call_result.TriggerMessage(
            status=self._trigger_message_response_status
        )

    @on(Action.certificate_signed)
    async def on_certificate_signed(self, certificate_chain, certificate_type=None, **kwargs):
        logging.info(f"Received CertificateSignedRequest: chain length={len(certificate_chain)}")
        self._certificate_signed_data = {
            'certificate_chain': certificate_chain,
            'certificate_type': certificate_type,
        }
        self._received_certificate_signed.set()
        return call_result.CertificateSigned(
            status=self._certificate_signed_response_status
        )

    @on(Action.get_variables)
    async def on_get_variables(self, get_variable_data, **kwargs):
        logging.info(f"Received GetVariablesRequest: {get_variable_data}")
        self._get_variables_data = get_variable_data
        self._received_get_variables.set()

        results = []
        for item in get_variable_data:
            component = item.get('component', {}) if isinstance(item, dict) else {}
            variable = item.get('variable', {}) if isinstance(item, dict) else {}
            key = f"{component.get('name', '')}.{variable.get('name', '')}"
            results.append({
                'attribute_status': GetVariableStatusEnumType.accepted,
                'attribute_value': self._get_variables_values.get(key, '0'),
                'component': component,
                'variable': variable,
            })

        return call_result.GetVariables(get_variable_result=results)

    @on(Action.get_base_report)
    async def on_get_base_report(self, request_id, report_base, **kwargs):
        logging.info(f"Received GetBaseReportRequest: request_id={request_id}, report_base={report_base}")
        self._get_base_report_data = {'request_id': request_id, 'report_base': report_base}
        self._received_get_base_report.set()
        return call_result.GetBaseReport(
            status=GenericDeviceModelStatusEnumType.accepted
        )

    @on(Action.get_report)
    async def on_get_report(self, request_id, **kwargs):
        logging.info(f"Received GetReportRequest: request_id={request_id}, kwargs={kwargs}")
        self._get_report_data = {'request_id': request_id, **kwargs}
        self._received_get_report.set()
        return call_result.GetReport(
            status=self._get_report_response_status
        )

    @on(Action.reset)
    async def on_reset(self, type, evse_id=None, **kwargs):
        logging.info(f"Received ResetRequest: type={type}, evse_id={evse_id}")
        self._reset_data = {'type': type, 'evse_id': evse_id}
        self._received_reset.set()
        return call_result.Reset(
            status=self._reset_response_status
        )

    @on(Action.clear_cache)
    async def on_clear_cache(self, **kwargs):
        logging.info(f"Received ClearCacheRequest, responding with {self._clear_cache_response_status}")
        self._received_clear_cache.set()
        return call_result.ClearCache(
            status=self._clear_cache_response_status
        )

    @on(Action.send_local_list)
    async def on_send_local_list(self, version_number, update_type, local_authorization_list=None, **kwargs):
        logging.info(f"Received SendLocalListRequest: version={version_number}, type={update_type}, "
                     f"entries={len(local_authorization_list) if local_authorization_list else 0}")
        self._send_local_list_data = {
            'version_number': version_number,
            'update_type': update_type,
            'local_authorization_list': local_authorization_list or [],
        }
        self._received_send_local_list.set()
        return call_result.SendLocalList(
            status=self._send_local_list_response_status
        )

    @on(Action.get_local_list_version)
    async def on_get_local_list_version(self, **kwargs):
        logging.info(f"Received GetLocalListVersionRequest, responding with version {self._local_list_version}")
        self._received_get_local_list_version.set()
        return call_result.GetLocalListVersion(
            version_number=self._local_list_version
        )

    @on(Action.request_stop_transaction)
    async def on_request_stop_transaction(self, transaction_id, **kwargs):
        logging.info(f"Received RequestStopTransactionRequest: transaction_id={transaction_id}")
        self._request_stop_transaction_data = {'transaction_id': transaction_id}
        self._received_request_stop_transaction.set()
        return call_result.RequestStopTransaction(
            status=self._request_stop_transaction_response_status
        )

    @on(Action.get_transaction_status)
    async def on_get_transaction_status(self, transaction_id=None, **kwargs):
        logging.info(f"Received GetTransactionStatusRequest: transaction_id={transaction_id}")
        self._get_transaction_status_data = {'transaction_id': transaction_id}
        self._received_get_transaction_status.set()
        return call_result.GetTransactionStatus(
            messages_in_queue=self._get_transaction_status_messages_in_queue,
            ongoing_indicator=self._get_transaction_status_ongoing_indicator,
        )

    @on(Action.request_start_transaction)
    async def on_request_start_transaction(self, id_token, remote_start_id, evse_id=None,
                                           group_id_token=None, charging_profile=None, **kwargs):
        logging.info(f"Received RequestStartTransactionRequest: id_token={id_token}, "
                     f"remote_start_id={remote_start_id}, evse_id={evse_id}")
        self._request_start_transaction_data = {
            'id_token': id_token,
            'remote_start_id': remote_start_id,
            'evse_id': evse_id,
            'group_id_token': group_id_token,
            'charging_profile': charging_profile,
        }
        self._received_request_start_transaction.set()
        return call_result.RequestStartTransaction(
            status=self._request_start_transaction_response_status,
            transaction_id=self._request_start_transaction_response_transaction_id,
        )

    @on(Action.unlock_connector)
    async def on_unlock_connector(self, evse_id, connector_id, **kwargs):
        logging.info(f"Received UnlockConnectorRequest: evse_id={evse_id}, connector_id={connector_id}")
        self._unlock_connector_data = {
            'evse_id': evse_id,
            'connector_id': connector_id,
        }
        self._received_unlock_connector.set()
        return call_result.UnlockConnector(
            status=self._unlock_connector_response_status,
        )

    @on(Action.change_availability)
    async def on_change_availability(self, operational_status, evse=None, **kwargs):
        logging.info(f"Received ChangeAvailabilityRequest: operational_status={operational_status}, evse={evse}")
        self._change_availability_data = {
            'operational_status': operational_status,
            'evse': evse,
        }
        self._received_change_availability.set()
        return call_result.ChangeAvailability(
            status=self._change_availability_response_status
        )

    @on(Action.reserve_now)
    async def on_reserve_now(self, id, expiry_date_time, id_token, connector_type=None,
                             evse_id=None, group_id_token=None, **kwargs):
        logging.info(f"Received ReserveNowRequest: id={id}, evse_id={evse_id}, id_token={id_token}")
        self._reserve_now_data = {
            'id': id,
            'expiry_date_time': expiry_date_time,
            'id_token': id_token,
            'connector_type': connector_type,
            'evse_id': evse_id,
            'group_id_token': group_id_token,
        }
        self._received_reserve_now.set()
        return call_result.ReserveNow(
            status=self._reserve_now_response_status
        )

    @on(Action.cancel_reservation)
    async def on_cancel_reservation(self, reservation_id, **kwargs):
        logging.info(f"Received CancelReservationRequest: reservation_id={reservation_id}")
        self._cancel_reservation_data = {
            'reservation_id': reservation_id,
        }
        self._received_cancel_reservation.set()
        return call_result.CancelReservation(
            status=self._cancel_reservation_response_status
        )

    @on(Action.cost_updated)
    async def on_cost_updated(self, total_cost, transaction_id, **kwargs):
        logging.info(f"Received CostUpdatedRequest: total_cost={total_cost}, transaction_id={transaction_id}")
        self._cost_updated_data = {
            'total_cost': total_cost,
            'transaction_id': transaction_id,
        }
        self._received_cost_updated.set()
        return call_result.CostUpdated()

    async def send_reservation_status_update(self, reservation_id, reservation_update_status):
        payload = call.ReservationStatusUpdate(
            reservation_id=reservation_id,
            reservation_update_status=reservation_update_status,
        )
        return await self.call(payload)

    async def send_meter_values(
        self,
        evse_id,
        sampled_values=None,
        skip_schema_validation=False,
        timestamp=None,
    ):
        if sampled_values is None:
            sampled_values = [{'value': 0.0, 'context': 'Trigger'}]
        payload = call.MeterValues(
            evse_id=evse_id,
            meter_value=[{
                'timestamp': timestamp or now_iso(),
                'sampled_value': sampled_values,
            }],
        )
        return await self.call(payload, skip_schema_validation=skip_schema_validation)

    async def send_log_status_notification_request(self, status='Idle'):
        payload = call.LogStatusNotification(status=status)
        return await self.call(payload)

    async def send_firmware_status_notification_request(self, status='Idle'):
        payload = call.FirmwareStatusNotification(status=status)
        return await self.call(payload)

    async def send_data_transfer(self, vendor_id, message_id=None, data=None):
        payload = call.DataTransfer(vendor_id=vendor_id, message_id=message_id, data=data)
        return await self.call(payload)

    async def send_heartbeat_request(self):
        payload = call.Heartbeat()
        return await self.call(payload)

    @on(Action.update_firmware)
    async def on_update_firmware(self, request_id, firmware, retries=None, retry_interval=None, **kwargs):
        logging.info(f"Received UpdateFirmwareRequest: request_id={request_id}")
        self._update_firmware_data = {
            'request_id': request_id,
            'firmware': firmware,
            'retries': retries,
            'retry_interval': retry_interval,
        }
        self._received_update_firmware.set()
        return call_result.UpdateFirmware(
            status=self._update_firmware_response_status
        )

    @on(Action.publish_firmware)
    async def on_publish_firmware(self, location, checksum, request_id, retries=None,
                                  retry_interval=None, **kwargs):
        logging.info(f"Received PublishFirmwareRequest: request_id={request_id}, location={location}")
        self._publish_firmware_data = {
            'location': location,
            'checksum': checksum,
            'request_id': request_id,
            'retries': retries,
            'retry_interval': retry_interval,
        }
        self._received_publish_firmware.set()
        return call_result.PublishFirmware(
            status=self._publish_firmware_response_status
        )

    @on(Action.unpublish_firmware)
    async def on_unpublish_firmware(self, checksum, **kwargs):
        logging.info(f"Received UnpublishFirmwareRequest: checksum={checksum}")
        self._unpublish_firmware_data = {
            'checksum': checksum,
        }
        self._received_unpublish_firmware.set()
        return call_result.UnpublishFirmware(
            status=self._unpublish_firmware_response_status
        )

    async def send_publish_firmware_status_notification_request(self, status, location=None, request_id=None):
        kwargs = {'status': status}
        if location is not None:
            kwargs['location'] = location
        if request_id is not None:
            kwargs['request_id'] = request_id
        payload = call.PublishFirmwareStatusNotification(**kwargs)
        return await self.call(payload)

    @on(Action.install_certificate)
    async def on_install_certificate(self, certificate_type, certificate, **kwargs):
        logging.info(f"Received InstallCertificateRequest: certificate_type={certificate_type}")
        self._install_certificate_data = {
            'certificate_type': certificate_type,
            'certificate': certificate,
        }
        self._received_install_certificate.set()
        return call_result.InstallCertificate(
            status=self._install_certificate_response_status
        )

    @on(Action.get_installed_certificate_ids)
    async def on_get_installed_certificate_ids(self, certificate_type=None, **kwargs):
        logging.info(f"Received GetInstalledCertificateIdsRequest: certificate_type={certificate_type}")
        self._get_installed_certificate_ids_data = {
            'certificate_type': certificate_type,
        }
        self._received_get_installed_certificate_ids.set()
        return call_result.GetInstalledCertificateIds(
            status=self._get_installed_certificate_ids_response_status,
            certificate_hash_data_chain=self._get_installed_certificate_ids_response_chain,
        )

    @on(Action.delete_certificate)
    async def on_delete_certificate(self, certificate_hash_data, **kwargs):
        logging.info(f"Received DeleteCertificateRequest: hash_data={certificate_hash_data}")
        self._delete_certificate_data = {
            'certificate_hash_data': certificate_hash_data,
        }
        self._received_delete_certificate.set()
        return call_result.DeleteCertificate(
            status=self._delete_certificate_response_status
        )

    @on(Action.set_network_profile)
    async def on_set_network_profile(self, configuration_slot, connection_data, **kwargs):
        logging.info(f"Received SetNetworkProfileRequest: slot={configuration_slot}, "
                     f"connection_data={connection_data}")
        self._set_network_profile_data = {
            'configuration_slot': configuration_slot,
            'connection_data': connection_data,
        }
        self._received_set_network_profile.set()
        return call_result.SetNetworkProfile(
            status=self._set_network_profile_response_status
        )

    async def send_get_certificate_status_request(self, ocsp_request_data):
        payload = call.GetCertificateStatus(ocsp_request_data=ocsp_request_data)
        return await self.call(payload)

    async def send_get_15118_ev_certificate_request(self, iso15118_schema_version, action, exi_request):
        payload = call.Get15118EVCertificate(
            iso15118_schema_version=iso15118_schema_version,
            action=action,
            exi_request=exi_request,
        )
        return await self.call(payload)

    @on(Action.get_monitoring_report)
    async def on_get_monitoring_report(self, request_id, component_variable=None,
                                        monitoring_criteria=None, **kwargs):
        logging.info(f"Received GetMonitoringReportRequest: request_id={request_id}, "
                     f"monitoring_criteria={monitoring_criteria}, component_variable={component_variable}")
        self._get_monitoring_report_data = {
            'request_id': request_id,
            'component_variable': component_variable,
            'monitoring_criteria': monitoring_criteria,
        }
        self._received_get_monitoring_report.set()
        return call_result.GetMonitoringReport(
            status=self._get_monitoring_report_response_status
        )

    @on(Action.set_monitoring_base)
    async def on_set_monitoring_base(self, monitoring_base, **kwargs):
        logging.info(f"Received SetMonitoringBaseRequest: monitoring_base={monitoring_base}")
        self._set_monitoring_base_data = {
            'monitoring_base': monitoring_base,
        }
        self._received_set_monitoring_base.set()
        return call_result.SetMonitoringBase(
            status=self._set_monitoring_base_response_status
        )

    @on(Action.set_variable_monitoring)
    async def on_set_variable_monitoring(self, set_monitoring_data, **kwargs):
        logging.info(f"Received SetVariableMonitoringRequest: {set_monitoring_data}")
        self._set_variable_monitoring_data = set_monitoring_data
        self._received_set_variable_monitoring.set()

        if self._set_variable_monitoring_response_results is not None:
            return call_result.SetVariableMonitoring(
                set_monitoring_result=self._set_variable_monitoring_response_results
            )

        results = []
        for item in set_monitoring_data:
            if isinstance(item, dict):
                results.append({
                    'status': SetMonitoringStatusEnumType.accepted,
                    'type': item.get('type', 'Delta'),
                    'severity': item.get('severity', 0),
                    'component': item.get('component', {}),
                    'variable': item.get('variable', {}),
                })
            else:
                results.append({
                    'status': SetMonitoringStatusEnumType.accepted,
                    'type': 'Delta',
                    'severity': 0,
                    'component': {},
                    'variable': {},
                })
        return call_result.SetVariableMonitoring(set_monitoring_result=results)

    @on(Action.set_monitoring_level)
    async def on_set_monitoring_level(self, severity, **kwargs):
        logging.info(f"Received SetMonitoringLevelRequest: severity={severity}")
        self._set_monitoring_level_data = {
            'severity': severity,
        }
        self._received_set_monitoring_level.set()
        return call_result.SetMonitoringLevel(
            status=self._set_monitoring_level_response_status
        )

    @on(Action.clear_variable_monitoring)
    async def on_clear_variable_monitoring(self, id, **kwargs):
        logging.info(f"Received ClearVariableMonitoringRequest: id={id}")
        self._clear_variable_monitoring_data = {
            'id': id,
        }
        self._received_clear_variable_monitoring.set()

        if self._clear_variable_monitoring_response_results is not None:
            return call_result.ClearVariableMonitoring(
                clear_monitoring_result=self._clear_variable_monitoring_response_results
            )

        results = [ClearMonitoringStatusEnumType.accepted for _ in id]
        return call_result.ClearVariableMonitoring(clear_monitoring_result=results)

    @on(Action.customer_information)
    async def on_customer_information(self, request_id, report, clear,
                                       customer_certificate=None, id_token=None,
                                       customer_identifier=None, **kwargs):
        logging.info(f"Received CustomerInformationRequest: request_id={request_id}, "
                     f"report={report}, clear={clear}")
        self._customer_information_data = {
            'request_id': request_id,
            'report': report,
            'clear': clear,
            'customer_certificate': customer_certificate,
            'id_token': id_token,
            'customer_identifier': customer_identifier,
        }
        self._received_customer_information.set()
        return call_result.CustomerInformation(
            status=self._customer_information_response_status
        )

    @on(Action.get_log)
    async def on_get_log(self, log, log_type, request_id, retries=None,
                          retry_interval=None, **kwargs):
        logging.info(f"Received GetLogRequest: request_id={request_id}, log_type={log_type}")
        self._get_log_data = {
            'log': log,
            'log_type': log_type,
            'request_id': request_id,
            'retries': retries,
            'retry_interval': retry_interval,
        }
        self._received_get_log.set()
        return call_result.GetLog(
            status=self._get_log_response_status
        )

    async def send_notify_monitoring_report(self, request_id, seq_no, monitor=None, tbc=False):
        payload = call.NotifyMonitoringReport(
            request_id=request_id,
            seq_no=seq_no,
            generated_at=now_iso(),
            monitor=monitor,
            tbc=tbc,
        )
        return await self.call(payload)

    async def send_notify_customer_information(self, data, seq_no, request_id, tbc=False):
        payload = call.NotifyCustomerInformation(
            data=data,
            seq_no=seq_no,
            generated_at=now_iso(),
            request_id=request_id,
            tbc=tbc,
        )
        return await self.call(payload)

    @on(Action.set_display_message)
    async def on_set_display_message(self, message, **kwargs):
        logging.info(f"Received SetDisplayMessageRequest: {message}")
        self._set_display_message_data = {
            'message': message,
        }
        self._received_set_display_message.set()
        return call_result.SetDisplayMessage(
            status=self._set_display_message_response_status
        )

    @on(Action.get_display_messages)
    async def on_get_display_messages(self, request_id, id=None, priority=None, state=None, **kwargs):
        logging.info(f"Received GetDisplayMessagesRequest: request_id={request_id}, id={id}, "
                     f"priority={priority}, state={state}")
        self._get_display_messages_data = {
            'request_id': request_id,
            'id': id,
            'priority': priority,
            'state': state,
        }
        self._received_get_display_messages.set()
        return call_result.GetDisplayMessages(
            status=self._get_display_messages_response_status
        )

    @on(Action.clear_display_message)
    async def on_clear_display_message(self, id, **kwargs):
        logging.info(f"Received ClearDisplayMessageRequest: id={id}")
        self._clear_display_message_data = {
            'id': id,
        }
        self._received_clear_display_message.set()
        return call_result.ClearDisplayMessage(
            status=self._clear_display_message_response_status
        )

    async def send_notify_display_messages(self, request_id, message_info=None, tbc=None):
        payload = call.NotifyDisplayMessages(
            request_id=request_id,
            message_info=message_info,
            tbc=tbc,
        )
        return await self.call(payload)
