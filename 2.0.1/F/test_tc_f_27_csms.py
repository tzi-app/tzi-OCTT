"""
TC_F_27 - Trigger message - NotImplemented
Use case: F06 | Requirements: F06.FR.08
F06.FR.08: When the Charging Station receives a TriggerMessageRequest with a requestedMessage that it has not implemented The Charging Station SHALL respond with TriggerMessageResponse with status NotImplemented.
    Precondition: When the Charging Station receives a TriggerMessageRequest with a requestedMessage that it has not implemented
System under test: CSMS

Description:
    The CSMS can request a Charging Station to send Charging Station-initiated messages. In the request
    the CSMS indicates which message it wishes to receive.

Purpose:
    To verify if the CSMS is able to handle a Charging Station that does not support the requested
    message value from a TriggerMessageRequest.

Main:
    1. CSMS sends TriggerMessageRequest
    2. CS responds with TriggerMessageResponse (status=NotImplemented)

Tool validations:
    N/a

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
    TriggerMessageStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_f_27():
    """Trigger message - NotImplemented."""
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
    # Configure the trigger message handler to respond with NotImplemented
    cp._trigger_message_response_status = TriggerMessageStatusEnumType.not_implemented
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available, evse_id=1)

    # Step 1-2: Wait for CSMS to send TriggerMessageRequest
    # The handler will automatically respond with NotImplemented
    await asyncio.wait_for(
        cp._received_trigger_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate that we received the trigger message
    assert cp._trigger_message_data is not None
    logging.info(f"Received TriggerMessageRequest for: {cp._trigger_message_data}")
    logging.info("Responded with status=NotImplemented")

    logging.info("TC_F_27 completed successfully")
    start_task.cancel()
    await ws.close()
