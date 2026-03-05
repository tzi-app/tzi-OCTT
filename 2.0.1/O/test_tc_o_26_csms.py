"""
TC_O_26 - Set Display Message - Rejected
Use case: O01 | Requirements: N/a
System under test: CSMS

Description:
    This test case describes how the CSMS can be requested to sent an SetDisplayMessageRequest to the
    charging station. Depending on the given parameters the message shall be displayed a certain way
    and at a certain moment on the Charging Station.

Purpose:
    To verify if the CSMS is able to send the request according to the DisplayMessage mechanism as
    described in the OCPP specification which gets rejected.

Main:
    Manual Action: Request the CSMS to send a SetDisplayMessageRequest with a Normal Cycle priority.
    1. The CSMS sends a SetDisplayMessageRequest
    2. The Test System responds with a SetDisplayMessageResponse with status Rejected

Tool validations:
    * Step 1: Message SetDisplayMessageRequest
      - message.id <Generated Id>
      - message.priority <Configured Priority>

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    DisplayMessageStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, build_default_ssl_context
from trigger import send_call

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_o_26():
    """Set Display Message - Rejected."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Respond with Rejected
    cp._set_display_message_response_status = DisplayMessageStatusEnumType.rejected

    # Trigger CSMS to send SetDisplayMessageRequest
    await send_call(cp_id, "SetDisplayMessage", {"message": {
        "id": 1, "priority": "NormalCycle", "state": "Idle",
        "message": {"format": "UTF8", "content": "Test message"},
    }})

    # Step 1-2: Wait for CSMS to send SetDisplayMessageRequest
    await asyncio.wait_for(
        cp._received_set_display_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._set_display_message_data is not None
    message = cp._set_display_message_data['message']

    # Tool validation: message.id must be present
    msg_id = message.get('id')
    assert msg_id is not None, "message.id must be present in SetDisplayMessageRequest"

    # Tool validation: message.priority must be present
    msg_priority = message.get('priority')
    assert msg_priority is not None, "message.priority must be present in SetDisplayMessageRequest"

    # CS responded with Rejected (handled by on_set_display_message handler)

    logging.info("TC_O_26 completed successfully")
    start_task.cancel()
    await ws.close()
