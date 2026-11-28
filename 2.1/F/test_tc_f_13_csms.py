"""
Test case name      Trigger message - TransactionEvent - Specific EVSE
Test case Id        TC_F_13_CSMS
Use case Id(s)      F06
Requirement(s)      F06.FR.01, F06.FR.02

Requirement Details:
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
    F06.FR.02: The CSMS MAY indicate to which EVSE this request applies.
        Precondition: F06.FR.01. For every such requested message.
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to trigger the Charging Station to send a
                    TransactionEventRequest for a specific EVSE, using a TriggerMessageRequest.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse with status Accepted
3. The Test System sends a TransactionEventRequest With
    - evse.id <Configured evseId>
    - triggerReason Trigger
    - transactionInfo.chargingState Charging
    - meterValue is present
    - meterValue[0].sampledValue.context Trigger
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage must be TransactionEvent
    - evse.id must be <Configured evseId>

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
from trigger import trigger_message
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_f_13(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # 1. The CSMS sends a TriggerMessageRequest
    # 2. The Test System responds with a TriggerMessageResponse with status Accepted
    cp.set_response('TriggerMessage', status='Accepted')
    request = await cp.wait_for_request(
        'TriggerMessage',
        manual_action=trigger_message(BASIC_AUTH_CP, 'TransactionEvent', evse_id=CONFIGURED_EVSE_ID))
    assert request.requested_message == 'TransactionEvent', \
        f"Expected TriggerMessageRequest.requestedMessage TransactionEvent, " \
        f"got {request.requested_message}"
    assert request.evse is not None and request.evse.id == CONFIGURED_EVSE_ID, \
        f"Expected TriggerMessageRequest.evse.id {CONFIGURED_EVSE_ID}, got {request.evse}"

    # 3. The Test System sends a TransactionEventRequest With
    #    - evse.id <Configured evseId>
    #    - triggerReason Trigger
    #    - transactionInfo.chargingState Charging
    #    - meterValue is present
    #    - meterValue[0].sampledValue.context Trigger
    # 4. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='Trigger',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'Charging'},
        evse={'id': CONFIGURED_EVSE_ID},
        meter_value=[{
            'timestamp': utc_now_iso(),
            'sampled_value': [{'value': 0.0, 'context': 'Trigger'}],
        }],
    ))

    start_task.cancel()
