"""
TC_E_30 - Check Transaction status - Transaction with id ongoing - without message in queue
Use case: E14 | Requirements: E14.FR.02, E14.FR.05
E14.FR.02: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has not stopped yet The Charging Station’s response SHALL have ongoingIndicator = true. E. Transactions
    Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has not stopped yet
E14.FR.05: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It has no transaction-related messages to be delivered about the transaction with that transactionId The Charging Station’s response SHALL have messagesInQueue = false.
    Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It has no transaction-related messages to be delivered about the transaction with that transactionId
System under test: CSMS

Purpose: Verify the CSMS can request the status of queued TransactionEventRequest messages from a
specific transaction by sending GetTransactionStatusRequest with a transactionId. The CS responds
that there are NO messages queued belonging to the ongoing transaction with the requested id.

Before: Reusable State EnergyTransferStarted

Test sequence:
1. CSMS sends GetTransactionStatusRequest with transactionId
2. CS responds with ongoingIndicator=true, messagesInQueue=false

Configuration:
    CSMS_ADDRESS     - WebSocket URL of the CSMS
    BASIC_AUTH_CP    - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD - Charge Point password
    VALID_ID_TOKEN   - Valid idToken value
    VALID_ID_TOKEN_TYPE - Valid idToken type
    CONFIGURED_EVSE_ID   - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID - Connector id (default 1)
    CSMS_ACTION_TIMEOUT - Seconds to wait for CSMS message (default 30)
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id
from trigger import send_call
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_e_30(connection):
    """Check Transaction status - ongoing without message in queue (E14.FR.02, E14.FR.05).
    E14.FR.02: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has not stopped yet The Charging Station’s response SHALL have ongoingIndicator = true. E. Transactions
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has not stopped yet
    E14.FR.05: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It has no transaction-related messages to be delivered about the transaction with that transactionId The Charging Station’s response SHALL have messagesInQueue = false.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It has no transaction-related messages to be delivered about the transaction with that transactionId
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    # Pre-configure response for GetTransactionStatus
    cp._get_transaction_status_ongoing_indicator = True
    cp._get_transaction_status_messages_in_queue = False
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Before: EnergyTransferStarted
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Drain CSMS-initiated messages (stale transaction checks from DB)
    await cp.drain_post_boot()

    # Step 1-2: Trigger CSMS to send GetTransactionStatusRequest
    async def trigger_get_status():
        await send_call(BASIC_AUTH_CP, "GetTransactionStatus",
                        {"transactionId": transaction_id})

    trigger_task = asyncio.create_task(trigger_get_status())

    await asyncio.wait_for(
        cp._received_get_transaction_status.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    # Validate transactionId in request
    assert cp._get_transaction_status_data is not None
    assert cp._get_transaction_status_data['transaction_id'] == transaction_id

    start_task.cancel()
