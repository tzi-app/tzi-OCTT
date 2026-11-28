"""
Test case name      Transactions with fixed cost, energy or time - CSMS calculates costs and specifies cost
                    limit
Test case Id        TC_E_109_CSMS
Use case Id(s)      E16
Requirement(s)      E16.FR.02, E16.FR.11

Requirement Details:
    E16.FR.02: CSMS SHALL include the field transactionLimit once in the first possible
               TransactionEventResponse message.
        Precondition: When CSMS sets or changes a limit to the transaction in cost, energy, SoC or time
        Note: transactionLimit uses maxCost for cost limit, maxEnergy for energy limit, maxTime for time limit
              or maxSoC for SoC limit.
    E16.FR.11: CSMS SHALL provide cost updates to Charging Station in TransactionEventResponse or
               CostUpdatedRequest.
        Precondition: When a transactionLimit.maxCost is active AND ( TariffCostCtrlr.Enabled[Tariff] = false
                      OR when CSMS has not provided a (default) tariff plan )
        Note: Central cost calculation is used.
System under test   CSMS

Description         CSMS will set a limit the transaction for the specified cost. CS will use central cost
                    calculation.

Purpose             To verify whether the CSMS correctly sends cost when central cost calculation is used.

Prerequisite(s)     - CSMS supports setting cost limits
                    - Test System has TxCtrlr.SupportedLimits containing maxCost
                    - Test System has TariffCostCtrlr.Enabled[Cost] is false

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession

Test Scenario
1. The Test System sends a AuthorizeRequest
    - With idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
2. The CSMS responds with a AuthorizeResponse
3. The Test System sends a TransactionEventRequest with
    - With eventType is Started
    - triggerReason is ChargingStateChanged
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
    - evse.id is <Configured evseId>
    - evse.connectorId is <Configured connectorId>
    - transactionInfo.transactionId is <transactionId>
    - transactionInfo.chargingState is Charging
4. The CSMS responds with a TransactionEventResponse
5 The Test System sends a TransactionEventRequest with
    - triggerReason is LimitSet
    - transactionInfo.transactionLimit.maxCost is 10
6 The CSMS responds with TransactionEventResponse
7. The CSMS sends a CostUpdatedRequest
8. The Test System responds with a CostUpdatedResponse

Note: Sending a CostUpdatedRequest is not required, but if CSMS does send it, the validation applies.

Tool validations
* Step 2:
    Message: AuthorizeResponse
    - idTokenInfo.status must be Accepted
* Step 4:
    Message: TransactionEventResponse
    - totalCost must be <not omitted>
    - transactionInfo.transactionLimit.maxEnergy must be <omitted>
    - transactionInfo.transactionLimit.maxTime must be <omitted>
    - transactionInfo.transactionLimit.maxCost must be 10
* Step 6:
    Message: TransactionEventResponse
    - totalCost must be <not omitted>
    - transactionInfo.transactionLimit must be <omitted>
* Step 8:
    Message: CostUpdatedRequest
    - transactionId must be <transactionId>
    - totalCost must be <not omitted>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import NO_ACTION_WAIT, TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from trigger import set_transaction_limit
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])

# The cost limit that the CSMS has for the transaction
MAX_COST = 10


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_109(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: Test System has TxCtrlr.SupportedLimits containing maxCost and
    # TariffCostCtrlr.Enabled[Cost] is false (the CSMS calculates the cost)
    cp.variables = {
        'TxCtrlr.SupportedLimits': 'maxCost',
        'TariffCostCtrlr.Enabled[Cost]': 'false',
    }
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EVConnectedPreSession
    # The transaction of this test case starts with the energy transfer (step 3), so the EV is
    # connected and there is no transaction yet.
    await ev_connected_pre_session(cp, starts_transaction=False)

    id_token = {'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE}

    # 1. The Test System sends a AuthorizeRequest
    #    - With idToken.idToken <Configured valid_idtoken_idtoken>
    #    - idToken.type <Configured valid_idtoken_type>
    # 2. The CSMS responds with a AuthorizeResponse
    response = await cp.call(call.Authorize(id_token=id_token))
    validate_id_token_info('AuthorizeResponse', response.id_token_info, status='Accepted')

    # Prerequisite: CSMS supports setting cost limits. It has a cost limit of 10 for this
    # transaction.
    await set_transaction_limit(BASIC_AUTH_CP, max_cost=MAX_COST)

    # 3. The Test System sends a TransactionEventRequest with
    #    - With eventType is Started
    #    - triggerReason is ChargingStateChanged
    #    - idToken.idToken <Configured valid_idtoken_idtoken>
    #    - idToken.type <Configured valid_idtoken_type>
    #    - evse.id is <Configured evseId>
    #    - evse.connectorId is <Configured connectorId>
    #    - transactionInfo.transactionId is <transactionId>
    #    - transactionInfo.chargingState is Charging
    # 4. The CSMS responds with a TransactionEventResponse
    transaction_id = cp.session.start_transaction()
    response = await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='ChargingStateChanged',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'Charging'},
        id_token=id_token,
        evse={'id': CONFIGURED_EVSE_ID, 'connector_id': CONFIGURED_CONNECTOR_ID},
    ))
    assert response.total_cost is not None, "TransactionEventResponse.totalCost must not be omitted"
    limit = response.transaction_limit
    assert limit is not None and limit.max_cost == MAX_COST, \
        f"Expected TransactionEventResponse.transactionLimit.maxCost {MAX_COST}, got {limit}"
    assert limit.max_energy is None, f"transactionLimit.maxEnergy must be omitted, got {limit.max_energy}"
    assert limit.max_time is None, f"transactionLimit.maxTime must be omitted, got {limit.max_time}"

    # 5. The Test System sends a TransactionEventRequest with
    #    - triggerReason is LimitSet
    #    - transactionInfo.transactionLimit.maxCost is 10
    # 6. The CSMS responds with TransactionEventResponse
    response = await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='LimitSet',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'transaction_limit': {'max_cost': MAX_COST}},
    ))
    assert response.total_cost is not None, "TransactionEventResponse.totalCost must not be omitted"
    assert response.transaction_limit is None, \
        f"TransactionEventResponse.transactionLimit must be omitted, got {response.transaction_limit}"

    # 7. The CSMS sends a CostUpdatedRequest
    # 8. The Test System responds with a CostUpdatedResponse
    # Note: Sending a CostUpdatedRequest is not required, but if CSMS does send it, the
    #       validation applies.
    try:
        await cp.wait_for_request('CostUpdated', timeout=NO_ACTION_WAIT)
    except asyncio.TimeoutError:
        pass
    for cost_updated in cp.requests_of('CostUpdated'):
        assert cost_updated.transaction_id == transaction_id, \
            f"Expected CostUpdatedRequest.transactionId {transaction_id}, " \
            f"got {cost_updated.transaction_id}"
        assert cost_updated.total_cost is not None, "CostUpdatedRequest.totalCost must not be omitted"

    start_task.cancel()
