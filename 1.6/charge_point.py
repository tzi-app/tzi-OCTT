import asyncio
import json
import logging
import sys

from ocpp.routing import on
from ocpp.v16 import ChargePoint, call, call_result
from ocpp.v16.enums import (
    Action,
    AvailabilityStatus,
    CancelReservationStatus,
    CertificateSignedStatus,
    CertificateStatus,
    ChargePointErrorCode,
    ChargePointStatus,
    ChargingProfileStatus,
    ClearCacheStatus,
    ClearChargingProfileStatus,
    ConfigurationStatus,
    DeleteCertificateStatus,
    DiagnosticsStatus,
    FirmwareStatus,
    GenericStatus,
    GetCompositeScheduleStatus,
    GetInstalledCertificateStatus,
    LogStatus,
    Reason,
    RemoteStartStopStatus,
    ReservationStatus,
    ResetStatus,
    ResetType,
    TriggerMessageStatus,
    UnlockStatus,
    UpdateFirmwareStatus,
    UpdateStatus,
    UploadLogStatus,
)

from utils import now_iso

logging.basicConfig(level=logging.INFO)

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


class TziChargePoint16(ChargePoint):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remote start
        self._received_remote_start = asyncio.Event()
        self._remote_start_id_tag = None
        self._remote_start_connector_id = None
        self._remote_start_response_status = RemoteStartStopStatus.accepted
        # Remote stop
        self._received_remote_stop = asyncio.Event()
        self._remote_stop_transaction_id = None
        self._remote_stop_response_status = RemoteStartStopStatus.accepted
        # Reset
        self._received_reset = asyncio.Event()
        self._reset_type = None
        # Unlock connector
        self._received_unlock_connector = asyncio.Event()
        self._unlock_connector_id = None
        self._unlock_response_status = UnlockStatus.unlocked
        # GetConfiguration
        self._received_get_configuration = asyncio.Event()
        self._get_configuration_keys = None
        self._configuration_key_list = []
        # ChangeConfiguration
        self._received_change_configuration = asyncio.Event()
        self._change_configuration_key = None
        self._change_configuration_value = None
        self._change_configuration_response_status = ConfigurationStatus.accepted
        # ChangeAvailability
        self._received_change_availability = asyncio.Event()
        self._change_availability_connector_id = None
        self._change_availability_type = None
        self._change_availability_response_status = AvailabilityStatus.accepted
        # ReserveNow
        self._received_reserve_now = asyncio.Event()
        self._reserve_now_data = None
        self._reserve_now_response_status = ReservationStatus.accepted
        # CancelReservation
        self._received_cancel_reservation = asyncio.Event()
        self._cancel_reservation_id = None
        self._cancel_reservation_response_status = CancelReservationStatus.accepted
        # TriggerMessage
        self._received_trigger_message = asyncio.Event()
        self._trigger_message_requested = None
        self._trigger_message_connector_id = None
        self._trigger_message_response_status = TriggerMessageStatus.accepted
        # SetChargingProfile
        self._received_set_charging_profile = asyncio.Event()
        self._set_charging_profile_data = None
        self._set_charging_profile_response_status = ChargingProfileStatus.accepted
        self._set_charging_profile_count = 0
        # ClearChargingProfile
        self._received_clear_charging_profile = asyncio.Event()
        self._clear_charging_profile_data = None
        self._clear_charging_profile_response_status = ClearChargingProfileStatus.accepted
        self._clear_charging_profile_count = 0
        # GetCompositeSchedule
        self._received_get_composite_schedule = asyncio.Event()
        self._get_composite_schedule_data = None
        self._get_composite_schedule_response = {}
        # UpdateFirmware
        self._received_update_firmware = asyncio.Event()
        self._update_firmware_data = None
        # GetDiagnostics
        self._received_get_diagnostics = asyncio.Event()
        self._get_diagnostics_data = None
        self._get_diagnostics_filename = 'diagnostics.log'
        # ClearCache
        self._received_clear_cache = asyncio.Event()
        self._clear_cache_response_status = ClearCacheStatus.accepted
        # SendLocalList
        self._received_send_local_list = asyncio.Event()
        self._send_local_list_data = None
        self._send_local_list_response_status = UpdateStatus.accepted
        self._send_local_list_count = 0
        # GetLocalListVersion
        self._received_get_local_list_version = asyncio.Event()
        self._local_list_version = 0
        # InstallCertificate
        self._received_install_certificate = asyncio.Event()
        self._install_certificate_data = None
        self._install_certificate_response_status = CertificateStatus.accepted
        # GetInstalledCertificateIds
        self._received_get_installed_certificate_ids = asyncio.Event()
        self._get_installed_certificate_ids_data = None
        self._get_installed_certificate_ids_response_status = GetInstalledCertificateStatus.accepted
        self._installed_certificate_hash_data = []
        # DeleteCertificate
        self._received_delete_certificate = asyncio.Event()
        self._delete_certificate_data = None
        self._delete_certificate_response_status = DeleteCertificateStatus.accepted
        # ExtendedTriggerMessage
        self._received_extended_trigger = asyncio.Event()
        self._extended_trigger_requested = None
        self._extended_trigger_response_status = TriggerMessageStatus.accepted
        # CertificateSigned
        self._received_certificate_signed = asyncio.Event()
        self._certificate_signed_chain = None
        self._certificate_signed_response_status = CertificateSignedStatus.accepted
        # SignedUpdateFirmware
        self._received_signed_update_firmware = asyncio.Event()
        self._signed_update_firmware_data = None
        self._signed_update_firmware_response_status = UpdateFirmwareStatus.accepted
        # GetLog
        self._received_get_log = asyncio.Event()
        self._get_log_data = None
        self._get_log_response_status = LogStatus.accepted

    async def call(self, payload, suppress=False, **kwargs):
        """Override default suppress=True so CALLERROR responses raise exceptions."""
        return await super().call(payload, suppress=suppress, **kwargs)

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

    # ── CP-initiated messages (requests TO the CSMS) ──

    async def send_boot_notification(self, vendor='tzi.app', model='CP Model 1.0'):
        payload = call.BootNotification(
            charge_point_vendor=vendor,
            charge_point_model=model,
        )
        return await self.call(payload)

    async def send_status_notification(self, connector_id,
                                       status=ChargePointStatus.available,
                                       error_code=ChargePointErrorCode.no_error):
        payload = call.StatusNotification(
            connector_id=connector_id,
            error_code=error_code,
            status=status,
            timestamp=now_iso(),
        )
        return await self.call(payload)

    async def send_heartbeat(self):
        payload = call.Heartbeat()
        return await self.call(payload)

    async def send_authorize(self, id_tag):
        payload = call.Authorize(id_tag=id_tag)
        return await self.call(payload)

    async def send_start_transaction(self, connector_id, id_tag, meter_start=0,
                                     reservation_id=None):
        payload = call.StartTransaction(
            connector_id=connector_id,
            id_tag=id_tag,
            meter_start=meter_start,
            timestamp=now_iso(),
            reservation_id=reservation_id,
        )
        return await self.call(payload)

    async def send_stop_transaction(self, transaction_id, meter_stop=0,
                                    reason=None, id_tag=None):
        payload = call.StopTransaction(
            transaction_id=transaction_id,
            meter_stop=meter_stop,
            timestamp=now_iso(),
            reason=reason,
            id_tag=id_tag,
        )
        return await self.call(payload)

    async def send_data_transfer(self, vendor_id, message_id=None, data=None):
        payload = call.DataTransfer(
            vendor_id=vendor_id,
            message_id=message_id,
            data=data,
        )
        return await self.call(payload)

    async def send_firmware_status_notification(self, status):
        payload = call.FirmwareStatusNotification(status=status)
        return await self.call(payload)

    async def send_diagnostics_status_notification(self, status):
        payload = call.DiagnosticsStatusNotification(status=status)
        return await self.call(payload)

    async def send_meter_values(self, connector_id, meter_value, transaction_id=None):
        payload = call.MeterValues(
            connector_id=connector_id,
            meter_value=meter_value,
            transaction_id=transaction_id,
        )
        return await self.call(payload)

    async def send_security_event_notification(self, event_type, tech_info=None):
        payload = call.SecurityEventNotification(
            type=event_type,
            timestamp=now_iso(),
            tech_info=tech_info,
        )
        return await self.call(payload)

    async def send_sign_certificate(self, csr):
        payload = call.SignCertificate(csr=csr)
        return await self.call(payload)

    async def send_signed_firmware_status_notification(self, status, request_id):
        payload = call.SignedFirmwareStatusNotification(
            status=status,
            request_id=request_id,
        )
        return await self.call(payload)

    async def send_log_status_notification(self, status, request_id):
        payload = call.LogStatusNotification(
            status=status,
            request_id=request_id,
        )
        return await self.call(payload)

    # ── CSMS-initiated messages (requests FROM the CSMS) ──

    @on(Action.remote_start_transaction)
    async def on_remote_start_transaction(self, id_tag, connector_id=None, **kwargs):
        logging.info(f"Received RemoteStartTransaction: id_tag={id_tag}, connector_id={connector_id}")
        self._remote_start_id_tag = id_tag
        self._remote_start_connector_id = connector_id
        self._remote_start_charging_profile = kwargs.get('charging_profile')
        self._received_remote_start.set()
        return call_result.RemoteStartTransaction(status=self._remote_start_response_status)

    @on(Action.remote_stop_transaction)
    async def on_remote_stop_transaction(self, transaction_id, **kwargs):
        logging.info(f"Received RemoteStopTransaction: transaction_id={transaction_id}")
        self._remote_stop_transaction_id = transaction_id
        self._received_remote_stop.set()
        return call_result.RemoteStopTransaction(status=self._remote_stop_response_status)

    @on(Action.reset)
    async def on_reset(self, type, **kwargs):
        logging.info(f"Received Reset: type={type}")
        self._reset_type = type
        self._received_reset.set()
        return call_result.Reset(status=ResetStatus.accepted)

    @on(Action.unlock_connector)
    async def on_unlock_connector(self, connector_id, **kwargs):
        logging.info(f"Received UnlockConnector: connector_id={connector_id}")
        self._unlock_connector_id = connector_id
        self._received_unlock_connector.set()
        return call_result.UnlockConnector(status=self._unlock_response_status)

    @on(Action.get_configuration)
    async def on_get_configuration(self, key=None, **kwargs):
        logging.info(f"Received GetConfiguration: key={key}")
        self._get_configuration_keys = key
        self._received_get_configuration.set()
        return call_result.GetConfiguration(
            configuration_key=self._configuration_key_list,
        )

    @on(Action.change_configuration)
    async def on_change_configuration(self, key, value, **kwargs):
        logging.info(f"Received ChangeConfiguration: key={key}, value={value}")
        self._change_configuration_key = key
        self._change_configuration_value = value
        self._received_change_configuration.set()
        return call_result.ChangeConfiguration(
            status=self._change_configuration_response_status,
        )

    @on(Action.change_availability)
    async def on_change_availability(self, connector_id, type, **kwargs):
        logging.info(f"Received ChangeAvailability: connector_id={connector_id}, type={type}")
        self._change_availability_connector_id = connector_id
        self._change_availability_type = type
        self._received_change_availability.set()
        return call_result.ChangeAvailability(status=self._change_availability_response_status)

    @on(Action.reserve_now)
    async def on_reserve_now(self, connector_id, expiry_date, id_tag, reservation_id, **kwargs):
        logging.info(f"Received ReserveNow: connector_id={connector_id}, id_tag={id_tag}, reservation_id={reservation_id}")
        self._reserve_now_data = {
            'connector_id': connector_id,
            'expiry_date': expiry_date,
            'id_tag': id_tag,
            'reservation_id': reservation_id,
        }
        self._received_reserve_now.set()
        return call_result.ReserveNow(status=self._reserve_now_response_status)

    @on(Action.cancel_reservation)
    async def on_cancel_reservation(self, reservation_id, **kwargs):
        logging.info(f"Received CancelReservation: reservation_id={reservation_id}")
        self._cancel_reservation_id = reservation_id
        self._received_cancel_reservation.set()
        return call_result.CancelReservation(status=self._cancel_reservation_response_status)

    @on(Action.trigger_message)
    async def on_trigger_message(self, requested_message, connector_id=None, **kwargs):
        logging.info(f"Received TriggerMessage: requested_message={requested_message}, connector_id={connector_id}")
        self._trigger_message_requested = requested_message
        self._trigger_message_connector_id = connector_id
        self._received_trigger_message.set()
        return call_result.TriggerMessage(status=self._trigger_message_response_status)

    @on(Action.set_charging_profile)
    async def on_set_charging_profile(self, connector_id, cs_charging_profiles, **kwargs):
        logging.info(f"Received SetChargingProfile: connector_id={connector_id}")
        self._set_charging_profile_data = {
            'connector_id': connector_id,
            'cs_charging_profiles': cs_charging_profiles,
        }
        self._set_charging_profile_count += 1
        self._received_set_charging_profile.set()
        return call_result.SetChargingProfile(status=self._set_charging_profile_response_status)

    @on(Action.clear_charging_profile)
    async def on_clear_charging_profile(self, id=None, connector_id=None,
                                        charging_profile_purpose=None, stack_level=None, **kwargs):
        logging.info(f"Received ClearChargingProfile: id={id}")
        self._clear_charging_profile_data = {
            'id': id, 'connector_id': connector_id,
            'charging_profile_purpose': charging_profile_purpose,
            'stack_level': stack_level,
        }
        self._clear_charging_profile_count += 1
        self._received_clear_charging_profile.set()
        return call_result.ClearChargingProfile(status=self._clear_charging_profile_response_status)

    @on(Action.get_composite_schedule)
    async def on_get_composite_schedule(self, connector_id, duration, charging_rate_unit=None, **kwargs):
        logging.info(f"Received GetCompositeSchedule: connector_id={connector_id}, duration={duration}")
        self._get_composite_schedule_data = {
            'connector_id': connector_id,
            'duration': duration,
            'charging_rate_unit': charging_rate_unit,
        }
        self._received_get_composite_schedule.set()
        return call_result.GetCompositeSchedule(
            status=GetCompositeScheduleStatus.accepted,
            **self._get_composite_schedule_response,
        )

    @on(Action.update_firmware)
    async def on_update_firmware(self, location, retrieve_date, **kwargs):
        logging.info(f"Received UpdateFirmware: location={location}")
        self._update_firmware_data = {
            'location': location,
            'retrieve_date': retrieve_date,
        }
        self._received_update_firmware.set()
        return call_result.UpdateFirmware()

    @on(Action.get_diagnostics)
    async def on_get_diagnostics(self, location, **kwargs):
        logging.info(f"Received GetDiagnostics: location={location}")
        self._get_diagnostics_data = {'location': location, **kwargs}
        self._received_get_diagnostics.set()
        return call_result.GetDiagnostics(file_name=self._get_diagnostics_filename)

    @on(Action.clear_cache)
    async def on_clear_cache(self, **kwargs):
        logging.info("Received ClearCache")
        self._received_clear_cache.set()
        return call_result.ClearCache(status=self._clear_cache_response_status)

    @on(Action.send_local_list)
    async def on_send_local_list(self, list_version, update_type, local_authorization_list=None, **kwargs):
        logging.info(f"Received SendLocalList: version={list_version}, type={update_type}")
        self._send_local_list_data = {
            'list_version': list_version,
            'update_type': update_type,
            'local_authorization_list': local_authorization_list,
        }
        self._send_local_list_count += 1
        self._received_send_local_list.set()
        return call_result.SendLocalList(status=self._send_local_list_response_status)

    @on(Action.get_local_list_version)
    async def on_get_local_list_version(self, **kwargs):
        logging.info("Received GetLocalListVersion")
        self._received_get_local_list_version.set()
        return call_result.GetLocalListVersion(list_version=self._local_list_version)

    @on(Action.install_certificate)
    async def on_install_certificate(self, certificate_type, certificate, **kwargs):
        logging.info(f"Received InstallCertificate: type={certificate_type}")
        self._install_certificate_data = {
            'certificate_type': certificate_type,
            'certificate': certificate,
        }
        self._received_install_certificate.set()
        return call_result.InstallCertificate(status=self._install_certificate_response_status)

    @on(Action.get_installed_certificate_ids)
    async def on_get_installed_certificate_ids(self, certificate_type, **kwargs):
        logging.info(f"Received GetInstalledCertificateIds: type={certificate_type}")
        self._get_installed_certificate_ids_data = {'certificate_type': certificate_type}
        self._received_get_installed_certificate_ids.set()
        return call_result.GetInstalledCertificateIds(
            status=self._get_installed_certificate_ids_response_status,
            certificate_hash_data=self._installed_certificate_hash_data or None,
        )

    @on(Action.delete_certificate)
    async def on_delete_certificate(self, certificate_hash_data, **kwargs):
        logging.info(f"Received DeleteCertificate")
        self._delete_certificate_data = certificate_hash_data
        self._received_delete_certificate.set()
        return call_result.DeleteCertificate(status=self._delete_certificate_response_status)

    @on(Action.extended_trigger_message)
    async def on_extended_trigger_message(self, requested_message, connector_id=None, **kwargs):
        logging.info(f"Received ExtendedTriggerMessage: requested_message={requested_message}")
        self._extended_trigger_requested = requested_message
        self._received_extended_trigger.set()
        return call_result.ExtendedTriggerMessage(status=self._extended_trigger_response_status)

    @on(Action.certificate_signed)
    async def on_certificate_signed(self, certificate_chain, **kwargs):
        logging.info("Received CertificateSigned")
        self._certificate_signed_chain = certificate_chain
        self._received_certificate_signed.set()
        return call_result.CertificateSigned(status=self._certificate_signed_response_status)

    @on(Action.signed_update_firmware)
    async def on_signed_update_firmware(self, request_id, firmware, **kwargs):
        logging.info(f"Received SignedUpdateFirmware: request_id={request_id}")
        self._signed_update_firmware_data = {
            'request_id': request_id,
            'firmware': firmware,
        }
        self._received_signed_update_firmware.set()
        return call_result.SignedUpdateFirmware(status=self._signed_update_firmware_response_status)

    @on(Action.get_log)
    async def on_get_log(self, log, log_type, request_id, **kwargs):
        logging.info(f"Received GetLog: log_type={log_type}, request_id={request_id}")
        self._get_log_data = {
            'log': log,
            'log_type': log_type,
            'request_id': request_id,
        }
        self._received_get_log.set()
        return call_result.GetLog(status=self._get_log_response_status)
