"""
TC_F_20 - Trigger message - Heartbeat
Use case: F06 | Requirements: F06.FR.01
F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to receive.
System under test: CSMS

Description:
    The CSMS can request a Charging Station to send Charging Station-initiated messages. In the request
    the CSMS indicates which message it wishes to receive.

Purpose:
    To verify if the CSMS is able to trigger the Charging Station to send a HeartbeatRequest, using a
    TriggerMessageRequest.

Main:
    1. CSMS sends TriggerMessageRequest (requestedMessage=Heartbeat)
    2. CS responds with TriggerMessageResponse (status=Accepted)
    3. CS sends HeartbeatRequest
    4. CSMS responds with HeartbeatResponse

Tool validations:
    * Step 1: TriggerMessageRequest
      - requestedMessage must be Heartbeat

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
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
    MessageTriggerEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_f_20():
    """Trigger message - Heartbeat."""
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

    await cp.send_status_notification(1, ConnectorStatusEnumType.available, evse_id=1)

    # Step 1-2: Wait for CSMS to send TriggerMessageRequest
    await asyncio.wait_for(
        cp._received_trigger_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate Step 1: TriggerMessageRequest content
    assert cp._trigger_message_data == MessageTriggerEnumType.heartbeat or \
           cp._trigger_message_data == 'Heartbeat', \
        f"Expected requestedMessage=Heartbeat, got {cp._trigger_message_data}"

    # Step 3-4: CS sends HeartbeatRequest
    response = await cp.send_heartbeat_request()
    assert response is not None
    assert response.current_time is not None, "HeartbeatResponse must contain currentTime"

    logging.info("TC_F_20 completed successfully")
    start_task.cancel()
    await ws.close()
