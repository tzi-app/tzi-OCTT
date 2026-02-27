"""
Test case name      WebSocket Subprotocol negotiation
Test case Id        TC_088_CSMS
OCPP version        1.6J
System under test   Central System (SUT)
Document ref        CompliancyTestTool-TestCaseDocument-CSMS-Section3 (2025-11), Table 198, p.172-173

Description         OCPP-J imposes extra constraints on the WebSocket subprotocol

Purpose             To verify whether the Central System is able to select OCPP 1.6 as a supported
                    version, when also a different unsupported version is supported by the Charge
                    Point and relays this selection via the Sec-Websocket-Protocol header.

Prerequisite(s)     N/a

Before (Preparations):
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): N/a

Test Scenario
1. The Charge Point disconnects the WebSocket connection and reconnects by sending a HTTP
   upgrade request with the header;
   Sec-WebSocket-Protocol: ocpp0.1
2. The Central System rejects the connection attempt and does NOT upgrade the connection to
   a WebSocket connection.
3. The Charge Point disconnects the WebSocket connection and reconnects by sending a HTTP
   upgrade request with the header;
   Sec-WebSocket-Protocol: ocpp0.1,ocpp1.6
4. The Central System accepts the connection attempt and upgrades the connection to a
   WebSocket connection.

Tool validations:
    * Step 4:
        - The authorization header of the HTTP upgrade response must contain the header
          Sec-Websocket-Protocol, and it must comply to the following:
        - The header is formatted as follows; Sec-WebSocket-Protocol: ocpp1.6

Post scenario validations:
    N/a

NOTE: The official doc only validates Step 4. Step 2 rejection of unsupported-only subprotocol
      is implied by the scenario but has no explicit tool validation entry in the document.

NOTE: The official doc says "The authorization header of the HTTP upgrade response must contain
      the header Sec-Websocket-Protocol" — this is misleading. Sec-WebSocket-Protocol is NOT the
      Authorization header; it is a separate WebSocket negotiation header in the HTTP upgrade response.

NOTE: This test is a duplicate of test_tc_088_csms.py (same TC_088_CSMS scenario).
"""

import asyncio
import os
import pytest
import websockets
from websockets import InvalidStatusCode

from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ADDRESS = os.environ['CSMS_ADDRESS']


@pytest.mark.asyncio
async def test_ws_subprotocol_negotiation():
    # Step 1-2: Only unsupported subprotocol -> rejected
    with pytest.raises((InvalidStatusCode, Exception)):
        await websockets.connect(
            uri=f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}',
            subprotocols=['ocpp0.1'],
            extra_headers=get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD),
        )

    # Step 3-4: Unsupported + supported subprotocol -> accepted, selects ocpp1.6
    ws = await websockets.connect(
        uri=f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}',
        subprotocols=['ocpp0.1', 'ocpp1.6'],
        extra_headers=get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD),
    )
    assert ws.open
    assert ws.subprotocol == 'ocpp1.6'
    await ws.close()
