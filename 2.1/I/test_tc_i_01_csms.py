"""
Test case name      Show EV Driver running total cost during charging - costUpdatedRequest
Test case Id        TC_I_01_CSMS
Use case Id(s)      I02
Requirement(s)      I02.FR.01

Requirement Details:
    I02.FR.01: The CSMS SHALL send either a CostUpdatedRequest at a relevant interval/moment or return the
               running cost in a TransactionEventResponse. This might depend on the charging speed, running
               cost, etc.
System under test   CSMS

Description         While a transaction is ongoing, the driver wants to know how much the running total cost
                    is, updated at a relevant interval.

Purpose             To verify if the CSMS is able to correctly send the running total cost as described in the
                    OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System sends a TransactionEventRequest with
    - triggerReason Authorized
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
    - eventType Updated
4. The CSMS responds with a TransactionEventResponse
5. Execute Reusable State EVConnectedPreSession
6. Execute Reusable State EnergyTransferStarted
7. The Test System sends a TransactionEventRequest With
    - triggerReason is MeterValuePeriodic
    - eventType is Updated
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured sampled Meter Values interval>.
    - sampledValue.context is Sample.Periodic
    Note(s):
    _- This step will be executed every _<Configured sampled Meter Values interval>
    - The Test System will end the testcase after two MeterValues.
8. The CSMS responds with a TransactionEventResponse
9. The CSMS sends a CostUpdatedRequest
    Note(s):
    - This step will be executed after every TransactionEventResponse, if the message did not contain a
      totalCost.
10. The Test System responds with a CostUpdatedResponse

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
* Step 4:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - totalCost <Optional>
* Step 7:
    Message (Optional) CostUpdatedRequest
    - transactionId <Generated TransactionId>

Post scenario validations:
    - N/a

Remarks
Transcription note (not printed in the document): the tool validation for the CostUpdatedRequest is printed
under "Step 7", although the CSMS sends that message in step 9; it is kept as printed. In the scenario table,
step 10 (Charging Station column) is printed in the same row as step 9 (CSMS column); the two are listed here
in numerical order.
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
SAMPLED_METER_VALUES_INTERVAL = int(os.environ['SAMPLED_METER_VALUES_INTERVAL'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_i_01(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    id_token = {'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE}

    # 1. The Test System sends an AuthorizeRequest with
    #    - idToken.idToken <Configured valid_idtoken_idtoken>
    #    - idToken.type <Configured valid_idtoken_type>
    # 2. The CSMS responds with an AuthorizeResponse
    response = await cp.call(call.Authorize(id_token=id_token))
    validate_id_token_info('AuthorizeResponse', response.id_token_info, status='Accepted')

    # 3. The Test System sends a TransactionEventRequest with
    #    - triggerReason Authorized
    #    - idToken.idToken <Configured valid_idtoken_idtoken>
    #    - idToken.type <Configured valid_idtoken_type>
    #    - eventType Updated
    # 4. The CSMS responds with a TransactionEventResponse
    transaction_id = cp.session.start_transaction()
    response = await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='Authorized',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        id_token=id_token,
    ))
    # idTokenInfo.status Accepted, totalCost <Optional>
    validate_id_token_info('TransactionEventResponse', response.id_token_info, status='Accepted')
    cp.session.state = 'Authorized'
    cp.session.authorized = True
    cp.session.id_token = id_token

    # 5. Execute Reusable State EVConnectedPreSession
    await ev_connected_pre_session(cp)

    # 6. Execute Reusable State EnergyTransferStarted
    await energy_transfer_started(cp)

    # 7. The Test System sends a TransactionEventRequest With
    #    - triggerReason is MeterValuePeriodic
    #    - eventType is Updated
    #    - timestamp <The intervals between the timestamps of the received Meter Value messages
    #      equals the configured sampled Meter Values interval>.
    #    - sampledValue.context is Sample.Periodic
    #    Note(s): This step will be executed every <Configured sampled Meter Values interval>.
    #    The Test System will end the testcase after two MeterValues.
    # 8. The CSMS responds with a TransactionEventResponse
    # 9. The CSMS sends a CostUpdatedRequest
    #    Note(s): This step will be executed after every TransactionEventResponse, if the
    #    message did not contain a totalCost.
    # 10. The Test System responds with a CostUpdatedResponse
    for reading in (1000.0, 2000.0):
        await asyncio.sleep(SAMPLED_METER_VALUES_INTERVAL)
        # Only a CostUpdatedRequest that follows this meter value is the one of step 9.
        cp.forget_requests('CostUpdated')
        sampled_at = utc_now_iso()
        response = await cp.call(call.TransactionEvent(
            event_type='Updated',
            timestamp=sampled_at,
            trigger_reason='MeterValuePeriodic',
            seq_no=cp.next_seq_no(),
            transaction_info={'transaction_id': transaction_id},
            meter_value=[{
                'timestamp': sampled_at,
                'sampled_value': [{'value': reading, 'context': 'Sample.Periodic'}],
            }],
        ))
        if response.total_cost is None:
            # I02.FR.01: the running cost comes in a CostUpdatedRequest when it is not in the
            # TransactionEventResponse
            await cp.wait_for_request('CostUpdated')

    # (Optional) CostUpdatedRequest - transactionId <Generated TransactionId>
    for cost_updated in cp.requests_of('CostUpdated'):
        assert cost_updated.transaction_id == transaction_id, \
            f"Expected CostUpdatedRequest.transactionId {transaction_id}, " \
            f"got {cost_updated.transaction_id}"

    start_task.cancel()
