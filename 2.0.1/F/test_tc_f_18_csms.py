"""
TC_F_18 - Trigger message - FirmwareStatusNotification - Idle
Use case: F06 | Requirements: F06.FR.01
F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to receive.
System under test: CSMS

Description:
    The CSMS can request a Charging Station to send Charging Station-initiated messages. In the request
    the CSMS indicates which message it wishes to receive.

Purpose:
    To verify if the CSMS is able to trigger the Charging Station to send a
    FirmwareStatusNotificationRequest, using a TriggerMessageRequest.

Main:
    1. CSMS sends TriggerMessageRequest (requestedMessage=FirmwareStatusNotification)
    2. CS responds with TriggerMessageResponse (status=Accepted)
    3. CS sends FirmwareStatusNotificationRequest (status=Idle)
    4. CSMS responds with FirmwareStatusNotificationResponse

Tool validations:
    * Step 1: TriggerMessageRequest
      - requestedMessage must be FirmwareStatusNotification

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
from utils import get_basic_auth_headers, build_default_ssl_context
from trigger import send_call

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_f_18():
    """Trigger message - FirmwareStatusNotification - Idle."""
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

    await cp.send_status_notification(1, ConnectorStatusEnumType.available, evse_id=1)

    # Step 1-2: Trigger CSMS to send TriggerMessageRequest
    async def trigger_msg():
        await asyncio.sleep(1)
        await send_call(BASIC_AUTH_CP, "TriggerMessage", {
            "requestedMessage": "FirmwareStatusNotification",
        })

    trigger_task = asyncio.create_task(trigger_msg())

    await asyncio.wait_for(
        cp._received_trigger_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    # Validate Step 1: TriggerMessageRequest content
    assert cp._trigger_message_data == MessageTriggerEnumType.firmware_status_notification or \
           cp._trigger_message_data == 'FirmwareStatusNotification', \
        f"Expected requestedMessage=FirmwareStatusNotification, got {cp._trigger_message_data}"

    # Step 3-4: CS sends FirmwareStatusNotificationRequest (status=Idle)
    response = await cp.send_firmware_status_notification_request(status='Idle')
    assert response is not None

    logging.info("TC_F_18 completed successfully")
    start_task.cancel()
    await ws.close()
