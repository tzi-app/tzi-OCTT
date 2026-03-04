"""
TC_O_27 - Set Display Message - Specific transaction - Display message at StartTime
Use case: O02 | Requirements: N/a
System under test: CSMS

Description:
    This test case describes how the CSMS can be requested to sent an SetDisplayMessageRequest to the
    charging station. Depending on the given parameters the message shall be displayed a certain way
    and at a certain moment on the Charging Station.

Purpose:
    To verify if the CSMS is able to send the request with a startTime for a specific transaction
    according to the DisplayMessage mechanism as described in the OCPP specification.

Before:
    Reusable State: State is EnergyTransferStarted

Main:
    1. The CSMS sends a SetDisplayMessageRequest
    2. The Test System responds with a SetDisplayMessageResponse with status Accepted

Tool validations:
    * Step 1: Message SetDisplayMessageRequest
      - message.state is <omitted>
      - message.startDateTime is <Configured startDateTime>
      - message.endDateTime is <omitted>
      - message.transactionId is <Generated transactionId from Before>

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
    VALID_IDTOKEN_IDTOKEN     - Valid idToken (default TEST_TOKEN_1)
    VALID_IDTOKEN_TYPE        - Valid idToken type (default ISO14443)
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
)

from tzi_charge_point import TziChargePoint
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers, generate_transaction_id

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
VALID_IDTOKEN_IDTOKEN = os.environ['VALID_IDTOKEN_IDTOKEN']
VALID_IDTOKEN_TYPE = os.environ['VALID_IDTOKEN_TYPE']


@pytest.mark.asyncio
async def test_tc_o_27():
    """Set Display Message - Specific transaction - Display message at StartTime."""
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

    # Before: Execute Reusable State Authorized + EnergyTransferStarted
    transaction_id = generate_transaction_id()
    await authorized(cp, VALID_IDTOKEN_IDTOKEN, VALID_IDTOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Step 1-2: Wait for CSMS to send SetDisplayMessageRequest
    await asyncio.wait_for(
        cp._received_set_display_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._set_display_message_data is not None
    message = cp._set_display_message_data['message']

    # Tool validation: message.state must be omitted
    msg_state = message.get('state')
    assert msg_state is None, \
        f"message.state should be omitted, got {msg_state}"

    # Tool validation: message.startDateTime must be present
    msg_start_dt = message.get('start_date_time') or message.get('startDateTime')
    assert msg_start_dt is not None, \
        "message.startDateTime must be present in SetDisplayMessageRequest"

    # Tool validation: message.endDateTime must be omitted
    msg_end_dt = message.get('end_date_time') or message.get('endDateTime')
    assert msg_end_dt is None, \
        f"message.endDateTime should be omitted, got {msg_end_dt}"

    # Tool validation: message.transactionId must match
    msg_transaction_id = message.get('transaction_id') or message.get('transactionId')
    assert msg_transaction_id is not None, \
        "message.transactionId must be present in SetDisplayMessageRequest"
    assert msg_transaction_id == transaction_id, \
        f"Expected transactionId={transaction_id}, got {msg_transaction_id}"

    # CS responded with Accepted (handled by on_set_display_message handler)

    logging.info("TC_O_27 completed successfully")
    start_task.cancel()
    await ws.close()
