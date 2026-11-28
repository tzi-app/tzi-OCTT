"""
Test case name      Stop transaction options - StopAuthorized - Remote
Test case Id        TC_E_21_CSMS
Use case Id(s)      E06(S3) AND F03
Requirement(s)      E06.FR.03, F03.FR.01, F03.FR.09, F03.FR.10

Requirement Details:
    E06.FR.03: The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType =
               Ended) to the CSMS.
        Precondition: TxStopPoint contains: Authorized AND EV Driver is authorized to stop a transaction.
    F03.FR.01: The CSMS SHALL send a RequestStopTransactionRequest to the Charging Station with the
               transactionId of the transaction.
        Precondition: When the CSMS receives a remote stop transaction trigger (For example when terminating
                      using a smartphone app, exceeding a (non local) prepaid credit.)
    F03.FR.09: The Charging Station SHALL set the triggerReason to inform the CSMS about what triggered the
               event. What reason to use is described in the description of TriggerReasonEnumType.
        Precondition: When sending a TransactionEventRequest
        Note: Same as E06.FR.15
    F03.FR.10: (not found in OCPP 2.1 Part 2)
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the stop options.

Purpose             To verify if the CSMS is able to handle a Charging Station that stops a transaction when
                    it receives a RequestStopTransactionRequest.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual Action: Trigger the CSMS to request the Charging Station to stop the ongoing transaction.

1. The CSMS sends a RequestStopTransactionRequest
2. The Test System responds with a RequestStopTransactionResponse
    with status Accepted
3. The Test System sends a TransactionEventRequest.
    with triggerReason is RemoteStop
    transactionInfo.stoppedReason is Remote
    eventType is Ended
4. The CSMS responds with a TransactionEventResponse.

Tool validations
* Step 1:
    Message: RequestStopTransactionRequest
    - transactionId must equal <transactionId provided by the Test System in before state.>

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


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_21(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # Manual Action: Trigger the CSMS to request the Charging Station to stop the ongoing
    #                transaction.
    # 1. The CSMS sends a RequestStopTransactionRequest
    # 2. The Test System responds with a RequestStopTransactionResponse with status Accepted
    request = await cp.wait_for_request(
        'RequestStopTransaction',
        manual_action=send_call(BASIC_AUTH_CP, 'RequestStopTransaction',
                                {'transactionId': transaction_id}))
    assert request.transaction_id == transaction_id, \
        f"Expected RequestStopTransactionRequest.transactionId {transaction_id}, " \
        f"got {request.transaction_id}"

    # 3. The Test System sends a TransactionEventRequest.
    #    with triggerReason is RemoteStop
    #    transactionInfo.stoppedReason is Remote
    #    eventType is Ended
    # 4. The CSMS responds with a TransactionEventResponse.
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='RemoteStop',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'stopped_reason': 'Remote'},
    ))

    start_task.cancel()
