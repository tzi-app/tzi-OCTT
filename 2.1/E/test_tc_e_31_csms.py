"""
Test case name      Check Transaction status - Transaction with id ended - with message in queue
Test case Id        TC_E_31_CSMS
Use case Id(s)      E14
Requirement(s)      E14.FR.03, E14.FR.04

Requirement Details:
    E14.FR.03: The Charging Station’s response SHALL have ongoingIndicator = false.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The
                      transaction with that transactionId has stopped
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
                    an ended transaction with the requested id.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System closes the WebSocket connection.
2. The Test System waits a number of seconds equal to _<Configured Transaction duration>, then it will
   reconnect to the CSMS._
3. The Test System sends a StatusNotificationRequest
    - With evseId is <Configured evseId>
    - connectorId is <Configured connectorId>
    - connectorStatus is Available
4. The CSMS responds with a StatusNotificationResponse
5. The Test System sends a TransactionEventRequest
    - With eventType is Ended
    - offline is true
    - triggerReason is EVCommunicationLost
    - transactionInfo.chargingState is Idle
    - seqNo <Skips two sequence number values>
6. The CSMS responds with a TransactionEventResponse
7. The CSMS sends a GetTransactionStatusRequest
8. The Test System responds with a GetTransactionStatusResponse
    - With ongoingIndicator is false
    - messagesInQueue is true
9. The Test System sends a TransactionEventRequest
    - With triggerReason is StopAuthorized
    - eventType is Updated
    - offline is true
    - seqNo <This is the first of the two skipped values>
10. The CSMS responds with a TransactionEventResponse
11. The Test System sends a TransactionEventRequest
    - With triggerReason is ChargingStateChanged
    - transactionInfo.chargingState is EVConnected
    - eventType is Updated
    - offline is true
    - seqNo <This is the second of the two skipped values>
12. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 5:
    Message: GetTransactionStatusRequest
    - transactionId <Generated transactionId from Before>

Post scenario validations:
    N/a

Remarks
Transcriber's note (not printed in the document): the Tool validations are printed under "Step 5" although the
GetTransactionStatusRequest is step 7 of the scenario; this is kept as printed. In the scenario table, step 8
(Charging Station column) and step 7 (CSMS column) share one row; they are listed here in numeric order.
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
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_31(connection, reconnect):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # 1. The Test System closes the WebSocket connection.
    await cp.disconnect()

    # 2. The Test System waits a number of seconds equal to <Configured Transaction duration>,
    #    then it will reconnect to the CSMS.
    #    While the station is offline the stop of the transaction is authorized, the energy
    #    transfer stops and the EV is disconnected: three events, which are in the queue of the
    #    station when it reconnects.
    await asyncio.sleep(TRANSACTION_DURATION / 3)
    stop_authorized_at, stop_authorized_seq_no = utc_now_iso(), cp.next_seq_no()
    await asyncio.sleep(TRANSACTION_DURATION / 3)
    ev_connected_at, ev_connected_seq_no = utc_now_iso(), cp.next_seq_no()
    await asyncio.sleep(TRANSACTION_DURATION / 3)
    ended_at, ended_seq_no = utc_now_iso(), cp.next_seq_no()
    start_task = cp.use_connection(await reconnect(
        BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD)))

    # 3. The Test System sends a StatusNotificationRequest
    #    - With evseId is <Configured evseId>
    #    - connectorId is <Configured connectorId>
    #    - connectorStatus is Available
    # 4. The CSMS responds with a StatusNotificationResponse
    await cp.send_status_notification(CONFIGURED_CONNECTOR_ID, 'Available', evse_id=CONFIGURED_EVSE_ID)

    # 5. The Test System sends a TransactionEventRequest
    #    - With eventType is Ended
    #    - offline is true
    #    - triggerReason is EVCommunicationLost
    #    - transactionInfo.chargingState is Idle
    #    - seqNo <Skips two sequence number values>
    # 6. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=ended_at,
        trigger_reason='EVCommunicationLost',
        seq_no=ended_seq_no,
        offline=True,
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'Idle'},
    ))

    # 7. The CSMS sends a GetTransactionStatusRequest
    # 8. The Test System responds with a GetTransactionStatusResponse
    #    - With ongoingIndicator is false
    #    - messagesInQueue is true
    cp.set_response('GetTransactionStatus', ongoing_indicator=False, messages_in_queue=True)
    request = await cp.wait_for_request(
        'GetTransactionStatus',
        manual_action=send_call(BASIC_AUTH_CP, 'GetTransactionStatus',
                                {'transactionId': transaction_id}))
    assert request.transaction_id == transaction_id, \
        f"Expected GetTransactionStatusRequest.transactionId {transaction_id}, " \
        f"got {request.transaction_id}"

    # 9. The Test System sends a TransactionEventRequest
    #    - With triggerReason is StopAuthorized
    #    - eventType is Updated
    #    - offline is true
    #    - seqNo <This is the first of the two skipped values>
    # 10. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=stop_authorized_at,
        trigger_reason='StopAuthorized',
        seq_no=stop_authorized_seq_no,
        offline=True,
        transaction_info={'transaction_id': transaction_id},
    ))

    # 11. The Test System sends a TransactionEventRequest
    #     - With triggerReason is ChargingStateChanged
    #     - transactionInfo.chargingState is EVConnected
    #     - eventType is Updated
    #     - offline is true
    #     - seqNo <This is the second of the two skipped values>
    # 12. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=ev_connected_at,
        trigger_reason='ChargingStateChanged',
        seq_no=ev_connected_seq_no,
        offline=True,
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'EVConnected'},
    ))

    start_task.cancel()
