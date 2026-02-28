"""OCTT trigger HTTP API helpers for OCPP 1.6 tests.

These functions call the CSMS HTTP trigger endpoints to make the CSMS
send OCPP CALL messages to a connected charge point.
"""

import asyncio
import json
import os
import urllib.request

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']


def _derive_api_url():
    """Derive HTTP API URL from the WebSocket CSMS_ADDRESS."""
    url = CSMS_ADDRESS
    if url.startswith('wss://'):
        return url.replace('wss://', 'https://', 1)
    elif url.startswith('ws://'):
        return url.replace('ws://', 'http://', 1)
    return url


CSMS_API_URL = os.environ['CSMS_TRIGGER_ADDRESS']


async def trigger_v16(station_id, action, body=None):
    """Fire an OCTT trigger via HTTP POST.

    Sends the JSON body as the OCPP CALL payload to the charge point.

    Args:
        station_id: The charge point identifier
        action: The kebab-case action name (e.g., 'remote-start-transaction')
        body: Optional JSON payload dict

    Returns:
        The JSON response from the CSMS
    """
    url = f"{CSMS_API_URL}/api/octt/1.6/{station_id}/{action}"
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


async def set_basic_auth_password(station_id, password):
    """Set the BasicAuth password for a station in the CSMS."""
    url = f"{CSMS_API_URL}/api/octt/set-basic-auth-password"
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


async def create_token(token_id, status):
    """Create (or update) a token with the given status in the CSMS database.

    Only 'Expired' and 'Blocked' statuses are accepted by the CSMS.
    """
    url = f"{CSMS_API_URL}/api/octt/create-token"
    data = json.dumps({"token_id": token_id, "status": status}).encode()
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
