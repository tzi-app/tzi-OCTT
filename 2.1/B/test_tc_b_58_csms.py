"""
Test case name      WebSocket Subprotocol validation
Test case Id        TC_B_58_CSMS
Use case Id(s)      Part 4 - JSON over WebSockets implementation guide
Requirement(s)      Section 3.1.2. OCPP version
System under test   CSMS

Description         OCPP-J imposes extra constraints on the WebSocket subprotocol, detailed in the following
                    section 3.1.2.

Purpose             To verify whether the CSMS is able to select a supported OCPP version, when also a
                    different unsupported version is supported by the Charging Station and relays this
                    selection via the Sec-Websocket-Protocol header.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System disconnects the WebSocket connection and reconnects by sending a HTTP upgrade request with
   the header; Sec-WebSocket-Protocol: ocpp0.1
2. The CSMS rejects the connection attempt and does NOT upgrade the connection to a WebSocket connection.
3. The Test System disconnects the WebSocket connection and reconnects by sending a HTTP upgrade request with
   the header; Sec-WebSocket-Protocol: ocpp0.1,ocpp<Selected OCPP version>
4. The CSMS accepts the connection attempt and upgrades the connection to a WebSocket connection.

Tool validations
* Step 4:
    The authorization header of the HTTP upgrade response must contain the header Sec-Websocket-Protocol, and
    it must comply to the following:
    - The header is formatted as follows; Sec-WebSocket-Protocol: ocpp<Selected OCPP version>

Post scenario validations:
    N/a

Remarks
Section heading printed above the table: TC_B_58_CSMS: WebSocket Subprotocol negotiation
"""

import asyncio
import logging
import os

import pytest
from websockets import InvalidHandshake

from charge_point import connect_to_csms
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

SELECTED_OCPP_VERSION = 'ocpp2.1'


@pytest.mark.asyncio
async def test_tc_b_58():
    headers = get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD)

    # 1. The Test System sends a HTTP upgrade request with the header;
    #    Sec-WebSocket-Protocol: ocpp0.1
    # 2. The CSMS rejects the connection attempt and does NOT upgrade the connection to a
    #    WebSocket connection.
    try:
        ws = await connect_to_csms(BASIC_AUTH_CP, headers=headers, subprotocols=['ocpp0.1'])
    except InvalidHandshake as rejected:
        logging.info(f"CSMS rejected the HTTP upgrade request: {rejected!r}")
    else:
        # Part 4 (3.3 Server response) has the CSMS reject in another way: when it does not
        # agree to one of the offered subprotocols, it MUST complete the handshake with a
        # response without a Sec-WebSocket-Protocol header and then immediately close the
        # WebSocket connection. That is accepted as a rejection as well.
        try:
            assert ws.response_headers.get('Sec-WebSocket-Protocol') is None, \
                f"The CSMS selected a subprotocol for an offer of ocpp0.1 only: " \
                f"{ws.response_headers.get('Sec-WebSocket-Protocol')}"
            try:
                await asyncio.wait_for(ws.wait_closed(), timeout=5)
            except asyncio.TimeoutError:
                pytest.fail("The CSMS accepted a connection that only offered the subprotocol ocpp0.1")
        finally:
            await ws.close()

    # 3. The Test System sends a HTTP upgrade request with the header;
    #    Sec-WebSocket-Protocol: ocpp0.1,ocpp<Selected OCPP version>
    # 4. The CSMS accepts the connection attempt and upgrades the connection to a WebSocket
    #    connection.
    ws = await connect_to_csms(
        BASIC_AUTH_CP, headers=headers, subprotocols=['ocpp0.1', SELECTED_OCPP_VERSION])
    try:
        assert ws.open
        # The HTTP upgrade response must contain the header
        # Sec-WebSocket-Protocol: ocpp<Selected OCPP version>
        response_subprotocol = ws.response_headers.get('Sec-WebSocket-Protocol')
        assert response_subprotocol == SELECTED_OCPP_VERSION, \
            f"Expected response header Sec-WebSocket-Protocol: {SELECTED_OCPP_VERSION}, " \
            f"got: {response_subprotocol}"
    finally:
        await ws.close()
