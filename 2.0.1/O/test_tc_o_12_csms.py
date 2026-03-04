"""
TC_O_12 - Set Display Message - Replace DisplayMessage
Use case: O06 | Requirements: N/a
System under test: CSMS

Description:
    This test case describes how a CSO can replace a DisplayMessage that is previously configured in
    a Charging Station. Replace the message content, but also all the given parameters with the
    new one.

Purpose:
    To verify if the CSMS is able to request to replace a display message according to the
    DisplayMessage mechanism as described in the OCPP specification.

Before:
    Memory State: A display message is configured.

Main:
    Manual Action: Request the CSMS to sent a display message with the same id as already configured one.
    1. The CSMS sends a SetDisplayMessageRequest with message.id <Configured_Id>
       message.priority <Configured Priority>
    2. The Test System responds with a SetDisplayMessageResponse with status Accepted

Tool validations:
    * Step 2: Message SetDisplayMessageRequest
      - message.id <Configured_Id>
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

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_o_12():
    """Set Display Message - Replace DisplayMessage."""
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

    # Before: Set up a display message first
    cp._set_display_message_response_status = DisplayMessageStatusEnumType.accepted
    await asyncio.wait_for(
        cp._received_set_display_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    assert cp._set_display_message_data is not None
    configured_message = cp._set_display_message_data['message']
    configured_id = configured_message.get('id')

    # Reset event for the replacement message
    cp._received_set_display_message.clear()
    cp._set_display_message_data = None

    # Step 1-2: Wait for CSMS to send replacement SetDisplayMessageRequest
    await asyncio.wait_for(
        cp._received_set_display_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._set_display_message_data is not None
    message = cp._set_display_message_data['message']

    # Tool validation: message.id must match the configured id
    msg_id = message.get('id')
    assert msg_id is not None, "message.id must be present in SetDisplayMessageRequest"
    assert msg_id == configured_id, \
        f"Expected message.id={configured_id}, got {msg_id}"

    # Tool validation: message.priority must be present
    msg_priority = message.get('priority')
    assert msg_priority is not None, "message.priority must be present in SetDisplayMessageRequest"

    # CS responded with Accepted (handled by on_set_display_message handler)

    logging.info("TC_O_12 completed successfully")
    start_task.cancel()
    await ws.close()
