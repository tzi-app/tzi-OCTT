"""
TC_E_34 - Check Transaction status - Without transactionId - without message in queue
Use case: E14 | Requirements: E14.FR.06, E14.FR.08
E14.FR.06: The Charging Station receives a GetTransactionStatusRequest without a transactionId The Charging Station’s response SHALL NOT have ongoingIndicator set.
    Precondition: The Charging Station receives a GetTransactionStatusRequest without a transactionId
E14.FR.08: The Charging Station receives a GetTransactionStatusRequest without a transactionId AND It has no transaction-related messages to be delivered. The Charging Station's response SHALL have messagesInQueue = false.
    Precondition: The Charging Station receives a GetTransactionStatusRequest without a transactionId AND It has no transaction-related messages to be delivered
System under test: CSMS

Purpose: Verify the CSMS can request the status of queued TransactionEventRequest messages by
sending GetTransactionStatusRequest without a transactionId. The CS responds that there are NO
messages queued.

Test sequence:
1. CSMS sends GetTransactionStatusRequest (transactionId omitted)
2. CS responds with ongoingIndicator omitted, messagesInQueue=false

Configuration:
    CSMS_ADDRESS     - WebSocket URL of the CSMS
    BASIC_AUTH_CP    - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD - Charge Point password
    CSMS_ACTION_TIMEOUT - Seconds to wait for CSMS message (default 30)
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_e_34(connection):
    """Check Transaction status - without transactionId - without message in queue (E14.FR.06, E14.FR.08).
    E14.FR.06: The Charging Station receives a GetTransactionStatusRequest without a transactionId The Charging Station’s response SHALL NOT have ongoingIndicator set.
        Precondition: The Charging Station receives a GetTransactionStatusRequest without a transactionId
    E14.FR.08: The Charging Station receives a GetTransactionStatusRequest without a transactionId AND It has no transaction-related messages to be delivered. The Charging Station's response SHALL have messagesInQueue = false.
        Precondition: The Charging Station receives a GetTransactionStatusRequest without a transactionId AND It has no transaction-related messages to be delivered
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    # Pre-configure response for GetTransactionStatus (without transactionId)
    cp._get_transaction_status_ongoing_indicator = None  # Omitted
    cp._get_transaction_status_messages_in_queue = False
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send GetTransactionStatusRequest (no transactionId)
    await asyncio.wait_for(
        cp._received_get_transaction_status.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate transactionId is None/omitted in request
    assert cp._get_transaction_status_data is not None
    assert cp._get_transaction_status_data['transaction_id'] is None

    start_task.cancel()
