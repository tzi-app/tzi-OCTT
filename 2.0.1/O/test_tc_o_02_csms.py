"""
TC_O_02 - Get all Display Messages - Success
Use case: O03 | Requirements: N/a
System under test: CSMS

Description:
    This test case describes how a CSO can request all the installed DisplayMessages configured via
    OCPP in a Charging Station. The Charging Station can remove messages when they are out-dated, or
    transactions have ended. It can be very useful for a CSO to be able to view to current list of
    messages, so the CSO knows which messages are (still) configured.

Purpose:
    To verify if the CSMS is able to send the request to get the DisplayMessages according to the
    mechanism as described in the OCPP specification.

Before:
    Memory State: A display message is configured.

Main:
    1. The CSMS sends a GetDisplayMessagesRequest
    2. The Test System responds with a GetDisplayMessagesResponse with status Accepted
    3. The Test System sends a NotifyDisplayMessagesRequest
    4. The CSMS responds with a NotifyDisplayMessagesResponse

Tool validations:
    * Step 1: Message GetDisplayMessagesRequest
      - requestId <Generated Id>
      - id <Omitted>
      - priority <Omitted>
      - state <Omitted>

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
    MessagePriorityEnumType,
    MessageFormatEnumType,
    MessageStateEnumType,
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
async def test_tc_o_02():
    """Get all Display Messages - Success."""
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

    # Step 1-2: Wait for CSMS to send GetDisplayMessagesRequest
    await asyncio.wait_for(
        cp._received_get_display_messages.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_display_messages_data is not None
    request_id = cp._get_display_messages_data['request_id']

    # Tool validation: requestId must be present
    assert request_id is not None, "requestId must be present in GetDisplayMessagesRequest"

    # Tool validation: id, priority, state should be omitted
    assert cp._get_display_messages_data['id'] is None, \
        "id should be omitted in GetDisplayMessagesRequest"
    assert cp._get_display_messages_data['priority'] is None, \
        "priority should be omitted in GetDisplayMessagesRequest"
    assert cp._get_display_messages_data['state'] is None, \
        "state should be omitted in GetDisplayMessagesRequest"

    # CS responded with Accepted (handled by on_get_display_messages handler)

    # Step 3-4: Send NotifyDisplayMessagesRequest with the configured message
    response = await cp.send_notify_display_messages(
        request_id=request_id,
        message_info=[{
            'id': configured_id,
            'priority': configured_message.get('priority', MessagePriorityEnumType.normal_cycle),
            'message': configured_message.get('message', {
                'format': MessageFormatEnumType.utf8,
                'content': 'Test message',
            }),
            'state': configured_message.get('state', MessageStateEnumType.idle),
        }],
    )
    assert response is not None

    logging.info("TC_O_02 completed successfully")
    start_task.cancel()
    await ws.close()
