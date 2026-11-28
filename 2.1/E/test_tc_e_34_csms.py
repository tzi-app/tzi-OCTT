"""
Test case name      Check Transaction status - Without transactionId - without message in queue
Test case Id        TC_E_34_CSMS
Use case Id(s)      E14
Requirement(s)      E14.FR.06, E14.FR.08

Requirement Details:
    E14.FR.06: The Charging Station’s response SHALL NOT have ongoingIndicator set.
        Precondition: The Charging Station receives a GetTransactionStatusRequest without a transactionId
    E14.FR.08: The Charging Station’s response SHALL have messagesInQueue = false.
        Precondition: The Charging Station receives a GetTransactionStatusRequest without a transactionId AND
                      It has no transaction-related messages to be delivered
System under test   CSMS

Description         The CSMS is able to request the status of a transaction and to find out whether there are
                    queued transaction-related messages, using the GetTransactionStatusRequest message.

Purpose             To verify if the CSMS is able to request the status of queued TransactionEventRequest
                    messages by sending a GetTransactionStatusRequest without a transactionId. The Test System
                    will respond that there are NO message(s) queued.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a GetTransactionStatusRequest
2. The Test System responds with a GetTransactionStatusResponse With ongoingIndicator is omitted.
    messagesInQueue is false

Tool validations
* Step 1:
    Message: GetTransactionStatusRequest
    - transactionId must be omitted.

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_34(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a GetTransactionStatusRequest
    # 2. The Test System responds with a GetTransactionStatusResponse With ongoingIndicator is
    #    omitted, messagesInQueue is false
    cp.set_response('GetTransactionStatus', messages_in_queue=False)
    request = await cp.wait_for_request(
        'GetTransactionStatus', manual_action=send_call(BASIC_AUTH_CP, 'GetTransactionStatus'))
    assert request.transaction_id is None, \
        f"GetTransactionStatusRequest.transactionId must be omitted, got {request.transaction_id}"

    start_task.cancel()
