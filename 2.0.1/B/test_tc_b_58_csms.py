"""
Test case name      WebSocket Subprotocol validation
Test case Id        TC_B_58_CSMS
Use case Id(s)      Part 4 - JSON over WebSockets implementation guide
Requirement(s)      Section 3.1.2. The exact OCPP version MUST be specified in the Sec-Websocket-Protocol field.
System under test   CSMS

Description         OCPP-J imposes extra constraints on the WebSocket subprotocol.
Purpose             To verify whether the CSMS is able to select a supported OCPP version, when also a different
                    unsupported version is supported by the Charging Station and relays this selection via the
                    Sec-Websocket-Protocol header.

Prerequisite(s)     N/a

Test Scenario
1. The OCTT reconnects with header Sec-WebSocket-Protocol: ocpp0.1
2. The CSMS rejects the connection and does NOT upgrade to WebSocket
3. The OCTT reconnects with header Sec-WebSocket-Protocol: ocpp0.1,ocpp<Selected OCPP version>
4. The CSMS accepts the connection and upgrades to WebSocket

Tool validations
* Step 4:
    HTTP upgrade response must include:
    - Sec-WebSocket-Protocol: ocpp<Selected OCPP version>

Post scenario validations:
    N/a
"""

import os

import pytest
import websockets
from websockets import InvalidHandshake, InvalidStatusCode

from utils import get_basic_auth_headers, build_default_ssl_context

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP_B']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
async def test_tc_b_58():
    """WebSocket Subprotocol validation: CSMS rejects unsupported and selects supported OCPP version."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)
    ssl_ctx = build_default_ssl_context() if uri.startswith('wss://') else None

    # Step 1-2: Unsupported subprotocol only -> handshake must be rejected.
    with pytest.raises((InvalidStatusCode, InvalidHandshake)):
        await websockets.connect(
            uri=uri,
            subprotocols=['ocpp0.1'],
            extra_headers=headers,
            ssl=ssl_ctx,
        )

    # Step 3-4: Offer unsupported + supported -> CSMS must select supported OCPP version.
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp0.1', 'ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    try:
        assert ws.open
        assert ws.subprotocol == 'ocpp2.0.1', \
            f"Expected negotiated subprotocol 'ocpp2.0.1', got: {ws.subprotocol}"

        response_subprotocol = ws.response_headers.get('Sec-WebSocket-Protocol')
        assert response_subprotocol == 'ocpp2.0.1', \
            f"Expected response header Sec-WebSocket-Protocol: ocpp2.0.1, got: {response_subprotocol}"
    finally:
        await ws.close()
