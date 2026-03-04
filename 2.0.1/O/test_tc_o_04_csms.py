"""
TC_O_04 - Clear Display Message - Success
Use case: O05 | Requirements: N/a
System under test: CSMS

Description:
    This test case describes how a CSO can remove a specific message, configured via OCPP in a
    Charging Station.

Purpose:
    To verify if the CSMS is able to request the Charging Station to clear a message according to
    the mechanism as described in the OCPP specification.

Before:
    Memory State: A display message is configured.

Main:
    1. The CSMS sends a ClearDisplayMessageRequest
    2. The Test System responds with a ClearDisplayMessageResponse with status Accepted

Tool validations:
    * Step 1: Message ClearDisplayMessageRequest
      - id <Generated Id from set display message>

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
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_o_04():
    """Clear Display Message - Success."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Before: A display message must be configured first
    cp._set_display_message_response_status = DisplayMessageStatusEnumType.accepted
    await asyncio.wait_for(
        cp._received_set_display_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    assert cp._set_display_message_data is not None
    configured_message = cp._set_display_message_data['message']
    configured_id = configured_message.get('id')

    # Step 1-2: Wait for CSMS to send ClearDisplayMessageRequest
    await asyncio.wait_for(
        cp._received_clear_display_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._clear_display_message_data is not None

    # Tool validation: id must match the configured display message id
    clear_id = cp._clear_display_message_data['id']
    assert clear_id is not None, "id must be present in ClearDisplayMessageRequest"
    assert clear_id == configured_id, \
        f"Expected ClearDisplayMessage id={configured_id}, got {clear_id}"

    # CS responded with Accepted (handled by on_clear_display_message handler)

    logging.info("TC_O_04 completed successfully")
    start_task.cancel()
    await ws.close()
