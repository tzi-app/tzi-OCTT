"""
Test case name      Check Transaction status - Transaction with id ongoing - without message in queue
Test case Id        TC_E_30_CSMS
Use case Id(s)      E14
Requirement(s)      E14.FR.02, E14.FR.05

Requirement Details:
    E14.FR.02: The Charging Station’s response SHALL have ongoingIndicator = true.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The
                      transaction with that transactionId has not stopped yet
    E14.FR.05: The Charging Station’s response SHALL have messagesInQueue = false.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It
                      has no transaction-related messages to be delivered about the transaction with that
                      transactionId
System under test   CSMS

Description         The CSMS is able to request the status of a transaction and to find out whether there are
                    queued transaction-related messages, using the GetTransactionStatusRequest message.

Purpose             To verify if the CSMS is able to request the status of queued TransactionEventRequest
                    messages from a specific transaction by sending a GetTransactionStatusRequest with a
                    transactionId. The Test System will respond that there is NO message queued belonging to
                    the ongoing transaction with the requested id.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a GetTransactionStatusRequest
2. The Test System responds with a GetTransactionStatusResponse With ongoingIndicator is true
    messagesInQueue is false

Tool validations
* Step 1:
    Message: GetTransactionStatusRequest
    - transactionId must be <Generated transactionId from Before>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_30(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # 1. The CSMS sends a GetTransactionStatusRequest
    # 2. The Test System responds with a GetTransactionStatusResponse With ongoingIndicator is
    #    true, messagesInQueue is false
    cp.set_response('GetTransactionStatus', ongoing_indicator=True, messages_in_queue=False)
    request = await cp.wait_for_request(
        'GetTransactionStatus',
        manual_action=send_call(BASIC_AUTH_CP, 'GetTransactionStatus',
                                {'transactionId': transaction_id}))
    assert request.transaction_id == transaction_id, \
        f"Expected GetTransactionStatusRequest.transactionId {transaction_id}, " \
        f"got {request.transaction_id}"

    start_task.cancel()
