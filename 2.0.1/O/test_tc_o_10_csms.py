"""
TC_O_10 - Set Display Message - Specific transaction - UnknownTransaction
Use case: O02 | Requirements: N/a
System under test: CSMS

Description:
    This test case describes how a CSMS can attempt to set a DisplayMessage for a transactionId that
    the CS does not know. The CS will respond with a SetDisplayMessageResponse status of
    UnknownTransaction.

Purpose:
    To verify if the CSMS is able to send a display message correctly according to the mechanism
    as described in the OCPP specification for a specific transaction.

Prerequisite:
    If the CSMS supports sending a SetDisplayMessageRequest with a transactionId for a transaction
    that does not exist.

Before:
    Reusable State: State is EnergyTransferStarted

Main:
    Manual Action: Request the CSMS to send a display message for a specific transaction.
    1. The CSMS sends a SetDisplayMessageRequest
    2. The Test System responds with a SetDisplayMessageResponse with status UnknownTransaction

Tool validations:
    * Step 1: Message SetDisplayMessageRequest
      - message.transactionId not omit AND
      - message.priority <Configured Priority>

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
    DisplayMessageStatusEnumType,
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
async def test_tc_o_10():
    """Set Display Message - Specific transaction - UnknownTransaction."""
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

    # Respond with UnknownTransaction since the transactionId won't match
    cp._set_display_message_response_status = DisplayMessageStatusEnumType.unknown_transaction

    # Step 1-2: Wait for CSMS to send SetDisplayMessageRequest
    await asyncio.wait_for(
        cp._received_set_display_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._set_display_message_data is not None
    message = cp._set_display_message_data['message']

    # Tool validation: message.transactionId must not be omitted
    msg_transaction_id = message.get('transaction_id') or message.get('transactionId')
    assert msg_transaction_id is not None, \
        "message.transactionId must not be omitted in SetDisplayMessageRequest"

    # Tool validation: message.priority must be present
    msg_priority = message.get('priority')
    assert msg_priority is not None, "message.priority must be present in SetDisplayMessageRequest"

    # CS responded with UnknownTransaction (handled by on_set_display_message handler)

    logging.info("TC_O_10 completed successfully")
    start_task.cancel()
    await ws.close()
