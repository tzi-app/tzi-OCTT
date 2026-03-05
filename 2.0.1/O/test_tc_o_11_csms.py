"""
TC_O_11 - Get a Specific Display Message - Unknown parameters
Use case: O04 | Requirements: N/a
System under test: CSMS

Description:
    This test case describes how a CSO can request specific installed DisplayMessages configured via
    OCPP in a Charging Station.

Purpose:
    To verify if the CSMS is able to request a specific id message from the charging station
    according to the mechanism as described in the OCPP specification.

Prerequisite:
    If the CSMS is able to send a GetDisplayMessage with an unknown id.

Before:
    Memory State: A display message is configured.

Main:
    1. The CSMS sends a GetDisplayMessagesRequest
    2. The Test System responds with a GetDisplayMessagesResponse with status Unknown

Tool validations:
    * Step 1: Message GetDisplayMessagesRequest
      - id <A different generated Id>
      - requestId <Generated Id>

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
    GetDisplayMessagesStatusEnumType,
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
async def test_tc_o_11():
    """Get a Specific Display Message - Unknown parameters."""
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
    await send_call(cp_id, "SetDisplayMessage", {"message": {
        "id": 1, "priority": "NormalCycle",
        "message": {"format": "UTF8", "content": "Test display message"},
    }})
    await asyncio.wait_for(
        cp._received_set_display_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    assert cp._set_display_message_data is not None
    configured_message = cp._set_display_message_data['message']
    configured_id = configured_message.get('id')

    # Respond with Unknown since the id won't match any configured messages
    cp._get_display_messages_response_status = GetDisplayMessagesStatusEnumType.unknown

    # Step 1-2: Trigger CSMS to send GetDisplayMessagesRequest with unknown id
    await send_call(cp_id, "GetDisplayMessages", {"requestId": 1, "id": [9999]})
    await asyncio.wait_for(
        cp._received_get_display_messages.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_display_messages_data is not None

    # Tool validation: id must be present (a different generated id)
    msg_ids = cp._get_display_messages_data['id']
    assert msg_ids is not None, "id must be present in GetDisplayMessagesRequest"

    # Tool validation: id must be different from the configured message id
    if configured_id is not None:
        assert configured_id not in msg_ids, \
            f"id should be different from configured message id ({configured_id}), got {msg_ids}"

    # Tool validation: requestId must be present
    request_id = cp._get_display_messages_data['request_id']
    assert request_id is not None, "requestId must be present in GetDisplayMessagesRequest"

    # CS responded with Unknown (handled by on_get_display_messages handler)

    logging.info("TC_O_11 completed successfully")
    start_task.cancel()
    await ws.close()
