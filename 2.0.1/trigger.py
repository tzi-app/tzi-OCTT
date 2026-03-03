"""OCTT trigger HTTP API helpers for OCPP 2.0.1 tests.

These functions call the CSMS HTTP trigger endpoints to make the CSMS
send OCPP CALL messages to a connected charge point.
"""

import asyncio
import json
import os
import urllib.request

CSMS_TRIGGER_ADDRESS = os.environ['CSMS_TRIGGER_ADDRESS']


async def trigger_v201(station_id, action, body=None):
    """Fire an OCTT trigger via HTTP POST.

    Sends the JSON body as the OCPP CALL payload to the charge point.

    Args:
        station_id: The charge point identifier
        action: The kebab-case action name (e.g., 'update-basic-auth-password')
        body: Optional JSON payload dict

    Returns:
        The JSON response from the CSMS
    """
    url = f"{CSMS_TRIGGER_ADDRESS}/api/octt/2.0.1/{station_id}/{action}"
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


async def send_call(station_id, action, body=None):
    """Send an arbitrary OCPP CALL to a connected charge point.

    Uses the generic /call/:action endpoint.
    """
    url = f"{CSMS_TRIGGER_ADDRESS}/api/octt/2.0.1/{station_id}/call/{action}"
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


async def set_security_profile(station_id, security_profile):
    """Update the security profile for a station directly in the CSMS database."""
    url = f"{CSMS_TRIGGER_ADDRESS}/api/octt/2.0.1/{station_id}/set-security-profile"
    data = json.dumps({"security_profile": security_profile}).encode()
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


async def set_pending_boot(station_id, pending=True):
    """Set or clear the pending provisioning flag for a station."""
    url = f"{CSMS_TRIGGER_ADDRESS}/api/octt/2.0.1/{station_id}/set-pending-boot"
    data = json.dumps({"pending": pending}).encode()
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


async def set_items_per_message(station_id, get_variables=None, set_variables=None, get_report=None):
    """Set ItemsPerMessage limits for a connected station."""
    body = {}
    if get_variables is not None:
        body['get_variables'] = get_variables
    if set_variables is not None:
        body['set_variables'] = set_variables
    if get_report is not None:
        body['get_report'] = get_report
    url = f"{CSMS_TRIGGER_ADDRESS}/api/octt/2.0.1/{station_id}/set-items-per-message"
    data = json.dumps(body).encode()
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


async def get_variables(station_id, get_variable_data):
    """Send batched GetVariablesRequest(s) respecting ItemsPerMessage limits."""
    url = f"{CSMS_TRIGGER_ADDRESS}/api/octt/2.0.1/{station_id}/get-variables"
    data = json.dumps({"getVariableData": get_variable_data}).encode()
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


async def set_variables(station_id, set_variable_data):
    """Send batched SetVariablesRequest(s) respecting ItemsPerMessage limits."""
    url = f"{CSMS_TRIGGER_ADDRESS}/api/octt/2.0.1/{station_id}/set-variables"
    data = json.dumps({"setVariableData": set_variable_data}).encode()
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
    url = f"{CSMS_TRIGGER_ADDRESS}/api/octt/set-basic-auth-password"
    data = json.dumps({"station_id": station_id, "password": password}).encode()
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
