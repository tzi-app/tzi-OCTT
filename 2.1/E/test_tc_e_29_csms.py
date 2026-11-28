"""
Test case name      Check Transaction status - Transaction with id ongoing - with message in queue
Test case Id        TC_E_29_CSMS
Use case Id(s)      E14
Requirement(s)      E14.FR.02, E14.FR.04

Requirement Details:
    E14.FR.02: The Charging Station’s response SHALL have ongoingIndicator = true.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The
                      transaction with that transactionId has not stopped yet
    E14.FR.04: The Charging Station’s response SHALL have messagesInQueue = true.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It
                      has transaction-related messages to be delivered about the transaction with that
                      transactionId
System under test   CSMS

Description         The CSMS is able to request the status of a transaction and to find out whether there are
                    queued transaction-related messages, using the GetTransactionStatusRequest message.

Purpose             To verify if the CSMS is able to request the status of queued TransactionEventRequest
                    messages from a specific transaction by sending a GetTransactionStatusRequest with a
                    transactionId. The Test System will respond that there are message(s) queued belonging to
                    the ongoing transaction with the requested id.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System closes the WebSocket connection.
2. The Test System waits a number of seconds equal to _<Configured Transaction Duration>, then it will
   reconnect to the CSMS._
3. The CSMS sends a GetTransactionStatusRequest
4. The Test System responds with a GetTransactionStatusResponse
    - With ongoingIndicator is true
    - messagesInQueue is true
5. The Test System sends a TransactionEventRequest
    - With eventType is Updated
    - meterValues is present.
    - offline is true
6. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 3:
    Message: GetTransactionStatusRequest
    - transactionId <Generated transactionId from Before>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_29(connection, reconnect):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # 1. The Test System closes the WebSocket connection.
    await cp.disconnect()

    # 2. The Test System waits a number of seconds equal to <Configured Transaction Duration>,
    #    then it will reconnect to the CSMS.
    await asyncio.sleep(TRANSACTION_DURATION)
    # The meter value that the station has in its queue was sampled while it was offline.
    sampled_at = utc_now_iso()
    start_task = cp.use_connection(await reconnect(
        BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD)))

    # 3. The CSMS sends a GetTransactionStatusRequest
    # 4. The Test System responds with a GetTransactionStatusResponse
    #    - With ongoingIndicator is true
    #    - messagesInQueue is true
    cp.set_response('GetTransactionStatus', ongoing_indicator=True, messages_in_queue=True)
    request = await cp.wait_for_request(
        'GetTransactionStatus',
        manual_action=send_call(BASIC_AUTH_CP, 'GetTransactionStatus',
                                {'transactionId': transaction_id}))
    assert request.transaction_id == transaction_id, \
        f"Expected GetTransactionStatusRequest.transactionId {transaction_id}, " \
        f"got {request.transaction_id}"

    # 5. The Test System sends a TransactionEventRequest
    #    - With eventType is Updated
    #    - meterValues is present.
    #    - offline is true
    # 6. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=sampled_at,
        trigger_reason='MeterValuePeriodic',
        seq_no=cp.next_seq_no(),
        offline=True,
        transaction_info={'transaction_id': transaction_id},
        meter_value=[{
            'timestamp': sampled_at,
            'sampled_value': [{'value': 1500.0, 'context': 'Sample.Periodic'}],
        }],
    ))

    start_task.cancel()
