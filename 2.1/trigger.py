"""OCTT trigger HTTP API helpers for OCPP 2.1 tests.

These functions call the CSMS HTTP trigger endpoints to make the CSMS
send OCPP CALL messages to a connected charge point.

A test passes the call to the mock station as the Manual Action of a step:

    request = await cp.wait_for_request(
        'Reset', manual_action=send_call(station_id, 'Reset', {'type': 'OnIdle'}))
"""

import asyncio
import json
import os
import urllib.request

CSMS_TRIGGER_ADDRESS = os.environ['CSMS_TRIGGER_ADDRESS']


async def _post(path, body=None):
    url = f"{CSMS_TRIGGER_ADDRESS}{path}"
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(
        None, lambda: urllib.request.urlopen(req, timeout=30)
    )
    return json.loads(resp.read().decode())


async def trigger_v21(station_id, action, body=None):
    """Fire an OCTT trigger via HTTP POST.

    Args:
        station_id: The charge point identifier
        action: The kebab-case action name (e.g., 'update-basic-auth-password')
        body: Optional JSON payload dict

    Returns:
        The JSON response from the CSMS
    """
    return await _post(f"/api/octt/2.1/{station_id}/{action}", body)


async def send_call(station_id, action, body=None):
    """Send an arbitrary OCPP CALL to a connected charge point.

    Uses the generic /call/:action endpoint. The body is the OCPP request payload, with the
    field names of the OCPP 2.1 schemas (camelCase).
    """
    return await _post(f"/api/octt/2.1/{station_id}/call/{action}", body)


async def trigger_message(station_id, requested_message, evse_id=None, connector_id=None,
                          custom_trigger=None):
    """Make the CSMS send a TriggerMessageRequest for requested_message, for an EVSE (and
    connector) when given. custom_trigger: the customTrigger of a CustomTrigger request."""
    body = {"requestedMessage": requested_message}
    if evse_id is not None:
        body["evse"] = {"id": evse_id}
        if connector_id is not None:
            body["evse"]["connectorId"] = connector_id
    if custom_trigger is not None:
        body["customTrigger"] = custom_trigger
    return await trigger_v21(station_id, 'trigger-message', body)


async def set_security_profile(station_id, security_profile):
    """Update the security profile for a station directly in the CSMS database."""
    return await trigger_v21(station_id, 'set-security-profile', {"security_profile": security_profile})


async def set_pending_boot(station_id, pending=True):
    """Set or clear the pending provisioning flag for a station."""
    return await trigger_v21(station_id, 'set-pending-boot', {"pending": pending})


async def get_variables(station_id, get_variable_data):
    """Send batched GetVariablesRequest(s) respecting ItemsPerMessage limits.

    The limits are the ones the station has reported to the CSMS, for example in the
    response to an earlier GetVariablesRequest for DeviceDataCtrlr.ItemsPerMessage."""
    return await trigger_v21(station_id, 'get-variables', {"getVariableData": get_variable_data})


async def set_variables(station_id, set_variable_data):
    """Send batched SetVariablesRequest(s) respecting ItemsPerMessage limits."""
    return await trigger_v21(station_id, 'set-variables', {"setVariableData": set_variable_data})


async def set_network_configuration(station_id, configuration_slot, connection_data):
    """Ask the CSMS to set a network configuration through the device model (B09, "Setting
    network configuration via device model"): it sends SetVariablesRequest(s) for the variables
    of the component NetworkConfiguration with instance <configuration_slot>, and sets
    ApnEnabled and VpnEnabled itself (B09.FR.29, B09.FR.30).

    connection_data is a NetworkConnectionProfileType, as in a SetNetworkProfileRequest."""
    return await trigger_v21(station_id, 'set-network-configuration', {
        "configurationSlot": configuration_slot,
        "connectionData": connection_data,
    })


async def set_transaction_limit(station_id, max_cost=None, max_energy=None, max_time=None,
                                max_soc=None, transaction_id=None):
    """Configure a limit in the CSMS for a transaction of the station (E16): a maximum cost,
    energy (Wh), time (seconds) or state of charge (%). Without transaction_id it is for the
    ongoing transaction of the station, or else for its next one. The CSMS sends the limit in
    the first possible TransactionEventResponse (E16.FR.02)."""
    limit = {"maxCost": max_cost, "maxEnergy": max_energy, "maxTime": max_time, "maxSoC": max_soc,
             "transactionId": transaction_id}
    return await trigger_v21(station_id, 'set-transaction-limit',
                             {name: value for name, value in limit.items() if value is not None})


async def provide_charging_profiles(station_id, enabled):
    """Turn on or off that the CSMS provides a charging profile for the charging needs of an
    EV at this station (K15 - K20). When it is off, the CSMS answers a
    NotifyEVChargingNeedsRequest of an ISO 15118-20 session with status NoChargingProfile
    (K18.FR.04, K19.FR.04)."""
    return await trigger_v21(station_id, 'provide-charging-profiles', {"enabled": enabled})


async def set_driver_tariff(id_token, id_token_type, tariff):
    """Configure the CSMS to provide a driver-specific tariff for an idToken (I08): tariff is
    a TariffType with the field names of the OCPP 2.1 schemas. tariff None removes it again.

    The call is not about one station: the tariff belongs to the idToken."""
    return await _post("/api/octt/2.1/driver-tariff", {
        "idToken": {"idToken": id_token, "type": id_token_type},
        "tariff": tariff,
    })


async def kiosk_payment_authorized(station_id, psp_ref, evse_id, card_last_4_digits,
                                   authorization_amount):
    """Tell the CSMS what a stand-alone payment terminal (Payment Kiosk) tells it when a payment
    card has been authorized for a Charging Station (C24): the reference of the payment at the
    PSP, the EVSE, payment details and the authorized amount. The CSMS then sends a
    RequestStartTransactionRequest with the PspRef as a DirectPayment idToken (C24.FR.01)."""
    return await trigger_v21(station_id, 'kiosk-payment-authorized', {
        "pspRef": psp_ref,
        "evseId": evse_id,
        "cardLast4Digits": card_last_4_digits,
        "authorizationAmount": authorization_amount,
    })


async def qr_code_payment(qr_url):
    """Tell the CSMS that an EV Driver visited its payment web page with the URL of a QR code,
    and paid at the PSP (C25). The CSMS validates the one-time password of the URL, decodes it,
    and for a valid URL sends a RequestStartTransactionRequest to the station of the URL
    (C25.FR.07, C25.FR.09, C25.FR.23).

    The call is not about one station: an invalid URL may not even name one."""
    return await _post("/api/octt/2.1/qr-code-payment", {"qrUrl": qr_url})


async def update_dynamic_schedule(station_id, charging_profile_id, interval, schedule_update):
    """Ask the CSMS to update a Dynamic charging profile that it has set at the station, from
    now on every `interval` seconds, with an UpdateDynamicScheduleRequest that has
    schedule_update (a ChargingScheduleUpdateType as on the wire). It does so until the
    charging profile is cleared (K28, Q04)."""
    return await trigger_v21(station_id, 'update-dynamic-schedule', {
        "chargingProfileId": charging_profile_id,
        "interval": interval,
        "scheduleUpdate": schedule_update,
    })


async def get_log(station_id, log_type, scheme='http', request_id=1):
    """Ask the CSMS for a GetLogRequest for a log that the station has to upload to the log
    server of the CSMS over `scheme` (http or https). The CSMS gives the remoteLocation, with
    the userinfo for HTTP Basic Authentication."""
    return await trigger_v21(station_id, 'get-log', {
        "logType": log_type, "scheme": scheme, "requestId": request_id})


async def clear_variable_monitoring(station_id, monitor_ids):
    """Ask the CSMS to clear these monitors. It sends as many ClearVariableMonitoringRequests as the
    station's ItemsPerMessageClearVariableMonitoring requires (N06.FR.04), and answers once the station
    has answered all of them."""
    return await trigger_v21(station_id, 'clear-variable-monitoring', {"id": monitor_ids})


async def reset(station_id, reset_type, evse_id=None):
    """Send a ResetRequest to a connected charge point."""
    body = {"type": reset_type}
    if evse_id is not None:
        body["evseId"] = evse_id
    return await send_call(station_id, "Reset", body)


async def get_report(station_id, component_criteria, component_variable, request_id=1):
    """Send a GetReportRequest to a connected charge point."""
    return await send_call(station_id, "GetReport", {
        "requestId": request_id,
        "componentCriteria": component_criteria,
        "componentVariable": component_variable,
    })


async def get_base_report(station_id, report_base, request_id=1):
    """Send a GetBaseReportRequest to a connected charge point."""
    return await send_call(station_id, "GetBaseReport", {
        "requestId": request_id,
        "reportBase": report_base,
    })


async def set_basic_auth_password(station_id, password):
    """Set the BasicAuth password for a station directly in the CSMS database."""
    return await _post("/api/octt/set-basic-auth-password",
                       {"station_id": station_id, "password": password})
