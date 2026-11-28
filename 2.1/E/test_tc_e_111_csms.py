"""
Test case name      Transactions with fixed cost, energy or time - CSMS specifies time limit
Test case Id        TC_E_111_CSMS
Use case Id(s)      E16
Requirement(s)      E16.FR.02

Requirement Details:
    E16.FR.02: CSMS SHALL include the field transactionLimit once in the first possible
               TransactionEventResponse message.
        Precondition: When CSMS sets or changes a limit to the transaction in cost, energy, SoC or time
        Note: transactionLimit uses maxCost for cost limit, maxEnergy for energy limit, maxTime for time limit
              or maxSoC for SoC limit.
System under test   CSMS

Description         CSMS will set a time limit on the transaction.

Purpose             To verify whether the CSMS is able to set a time limit.

Prerequisite(s)     - CSMS supports setting energy limits
                    - Test System has TxCtrlr.SupportedLimits containing maxTime

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession

Test Scenario
Manual action: In CSMS, configure time limit of duration <Configured time limit> for this transaction

1. The Test System sends a TransactionEventRequest with
    - With eventType is Started
    - triggerReason is ChargingStateChanged
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
    - evse.id is <Configured evseId>
    - evse.connectorId is <Configured connectorId>
    - transactionInfo.transactionId is <transactionId>
    - transactionInfo.chargingState is Charging
    - transactionInfo.transactionLimit <omitted>
2. The CSMS responds with a TransactionEventResponse
3. The Test System sends a TransactionEventRequest with
    - eventType is Updated
    - triggerReason is LimitSet
    - evse.id is <Configured evseId>
    - evse.connectorId is <Configured connectorId>
    - transactionInfo.transactionId is <transactionId>
    - transactionInfo.transactionLimit.maxEnergy <omitted>
    - transactionInfo.transactionLimit.maxTime <Configured time limit>
    - transactionInfo.transactionLimit.maxCost <omitted>
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted
    - transactionLimit.maxEnergy must be <omitted>
    - transactionLimit.maxTime must be <Configured time limit>
    - transactionLimit.maxCost must be <omitted>
* Step 4:
    Message: TransactionEventResponse
    - transactionLimit must be <omitted>

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.13. Page 1096/1097 - (2026-02) - TC_E_111_CSMS - Added missing Authorization request to initiate
        transaction
        An explicit authorization request was introduced for improved clarity, and the configured time limit
        was standardized to a fixed value.

        | Test case name | Transactions with fixed cost, energy or time - CSMS specifies time limit |
        | Test case Id | TC_E_111_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | 1. The Test System sends an AuthorizeRequest / With idToken.idToken <Configured
          valid_idtoken_idtoken> / idToken.type <Configured valid_idtoken_type> | 2. The CSMS responds with an
          AuthorizeResponse |
        | Manual action: In CSMS, configure time limit of duration [removed: <Configured time limit>] 120 for
          this transaction | |
        | [removed: 1.] 3. The Test System sends a TransactionEventRequest with / With eventType is Started /
          triggerReason is ChargingStateChanged / idToken.idToken <Configured valid_idtoken_idtoken> /
          idToken.type <Configured valid_idtoken_type> / evse.id is <Configured evseId> / evse.connectorId is
          <Configured connectorId> / transactionInfo.transactionId is <transactionId> /
          transactionInfo.chargingState is Charging / transactionInfo.transactionLimit <omitted> | [removed:
          2.] 4. The CSMS responds with a TransactionEventResponse |
        | [removed: 3.] 5. The Test System sends a TransactionEventRequest with / eventType is Updated /
          triggerReason is LimitSet / evse.id is <Configured evseId> / evse.connectorId is <Configured
          connectorId> / transactionInfo.transactionId is <transactionId> /
          transactionInfo.transactionLimit.maxEnergy <omitted> / transactionInfo.transactionLimit.maxTime
          [removed: <Configured time limit>] 120 / transactionInfo.transactionLimit.maxCost <omitted> |
          [removed: 4.] 6. The CSMS responds with a TransactionEventResponse |

        | Tool validations |
        | * Step [removed: 2] 4: / Message: TransactionEventResponse / idTokenInfo.status must be Accepted /
          transactionLimit.maxEnergy must be <omitted> / transactionLimit.maxTime must be [removed:
          <Configured time limit>] 120 / transactionLimit.maxCost must be <omitted> / * Step [removed: 4] 6: /
          Message: TransactionEventResponse / transactionLimit must be <omitted> |
        | Post scenario validations: / N/a |
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import TziChargePoint21
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

# The time limit of the scenario, in seconds (errata 2026-09, 6.3.13)
MAX_TIME = 120


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_111(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisite: Test System has TxCtrlr.SupportedLimits containing maxTime
    cp.variables = {'TxCtrlr.SupportedLimits': 'maxTime'}
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # The scenario is the one of errata 2026-09 (6.3.13), which added the AuthorizeRequest and
    # made the time limit 120.

    # Reusable State: State is EVConnectedPreSession
    # The transaction of this test case starts with the energy transfer (step 3), so the EV is
    # connected and there is no transaction yet.
    await ev_connected_pre_session(cp, starts_transaction=False)

    id_token = {'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE}

    # 1. The Test System sends an AuthorizeRequest
    #    With idToken.idToken <Configured valid_idtoken_idtoken>
    #    idToken.type <Configured valid_idtoken_type>
    # 2. The CSMS responds with an AuthorizeResponse
    await cp.call(call.Authorize(id_token=id_token))

    # Manual action: In CSMS, configure time limit of duration 120 for this transaction
    await set_transaction_limit(BASIC_AUTH_CP, max_time=MAX_TIME)

    # 3. The Test System sends a TransactionEventRequest with
    #    With eventType is Started
    #    triggerReason is ChargingStateChanged
    #    idToken.idToken <Configured valid_idtoken_idtoken>
    #    idToken.type <Configured valid_idtoken_type>
    #    evse.id is <Configured evseId>
    #    evse.connectorId is <Configured connectorId>
    #    transactionInfo.transactionId is <transactionId>
    #    transactionInfo.chargingState is Charging
    #    transactionInfo.transactionLimit <omitted>
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
    validate_id_token_info('TransactionEventResponse', response.id_token_info, status='Accepted')
    limit = response.transaction_limit
    assert limit is not None and limit.max_time == MAX_TIME, \
        f"Expected TransactionEventResponse.transactionLimit.maxTime {MAX_TIME}, got {limit}"
    assert limit.max_energy is None, f"transactionLimit.maxEnergy must be omitted, got {limit.max_energy}"
    assert limit.max_cost is None, f"transactionLimit.maxCost must be omitted, got {limit.max_cost}"

    # 5. The Test System sends a TransactionEventRequest with
    #    eventType is Updated
    #    triggerReason is LimitSet
    #    evse.id is <Configured evseId>
    #    evse.connectorId is <Configured connectorId>
    #    transactionInfo.transactionId is <transactionId>
    #    transactionInfo.transactionLimit.maxEnergy <omitted>
    #    transactionInfo.transactionLimit.maxTime 120
    #    transactionInfo.transactionLimit.maxCost <omitted>
    # 6. The CSMS responds with a TransactionEventResponse
    response = await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='LimitSet',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'transaction_limit': {'max_time': MAX_TIME}},
        evse={'id': CONFIGURED_EVSE_ID, 'connector_id': CONFIGURED_CONNECTOR_ID},
    ))
    assert response.transaction_limit is None, \
        f"TransactionEventResponse.transactionLimit must be omitted, got {response.transaction_limit}"

    start_task.cancel()
