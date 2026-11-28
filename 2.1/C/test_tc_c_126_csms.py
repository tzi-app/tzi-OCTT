"""
Test case name      Ad hoc payment via stand-alone payment terminal - local cost calculation
Test case Id        TC_C_126_CSMS
Use case Id(s)      C24
Requirement(s)      C24.FR.01, C24.FR.02, C24.FR.10

Requirement Details:
    C24.FR.01: CSMS SHALL send a RequestStartTransactionRequest to Charging Station with identity <CS> and
               EVSE <evse> (when present) and having idToken.idToken = <PspRef> and idToken.type =
               DirectPayment
        Precondition: When CSMS receives a message from Payment Kiosk that payment is authorized with
                      authorization reference <PspRef> for Charging Station with identity <CS> and optionally
                      an EVSE <evse>
        Note: There is need to include additionalInfo elements for payment details, like cardBin,
              cardLast4Digits, towards Charging Station. The protocol between Payment Kiosk and CSMS is not
              specified in this document.
    C24.FR.02: CSMS SHALL respond with a TransactionEventResponse with transactionLimit set to the required
               limit.
        Precondition: C24.FR.01 AND Charging Station sends a TransactionEventRequest with eventType = Started
        Note: transactionLimit uses maxCost for cost limit, maxEnergy for energy limit, maxTime for time limit
              or maxSoC for SoC limit.
    C24.FR.10: CSMS SHALL send a message to Payment Kiosk or PSP to settle the cost
        Precondition: After CSMS received a TransactionEventRequest with eventType = Ended or the transaction
        Note: Whether settling is done via Payment Kiosk or directly with PSP is depending on the
              implementation. Cost may have been calculated locally or centrally.
System under test   CSMS

Description         In order to test that Charging Station supports ad hoc payment via a stand-alone payment
                    terminal with local cost calculation.

Purpose             To verify that the CSMS can properly handle ad hoc payments made via a stand-alone payment
                    terminal when using local cost calculation.

Prerequisite(s)     - CSMS is connected with a stand-alone payment terminal
                    - Test System has AuthCtrlr.AuthorizeRemoteStart = false
                    - Test System has TariffCostCtrlr.Enabled[Cost] = true
                    - Test System has TariffCostCtrlr.Currency = "EUR"

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Present a payment card to the payment terminal Kiosk for Charging Station with identity
               <Configured unique Charging Station identifier>

1. The CSMS sends a RequestStartTransactionRequest
2. The Test System responds with a RequestStartTransactionResponse with
    - status Accepted
3. The Test System sends a TransactionEventRequest with
    - eventType Started
    - idToken <IdToken from step 1>
    - idToken.type DirectPayment
    - idToken.additionalInfo <additionalInfo>
    - transactionInfo.transactionId <transactionId>
4. The CSMS responds with a TransactionEventResponse

Settlement

5. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - idToken <IdToken from step 1>
    - idToken.type DirectPayment
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.transactionLimit.maxCost <not omitted>
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.fixed.exclTax 15.00
    - costDetails.totalCost.fixed.inclTax 18.15 EUR
    - costDetails.totalCost.fixed.taxRate.type MyTax
    - costDetails.totalCost.fixed.taxRate.tax 21
    - costDetails.totalUsage.energy 123
    - costDetails.totalUsage.chargingTime 5
    - costDetails.totalUsage.idleTime 0
    - costDetails.chargingPeriods <omitted>
6. The CSMS responds with a TransactionEventResponse

Note(s):
- The CSMS sends a message to Payment Kiosk or PSP to settle the cost for amount: 18.15 EUR

Tool validations
* Step 1:
    Message RequestStartTransactionRequest
    - evseId must be <evse>
    - remoteStartId must be <not omitted>
    - idToken.idToken must be <Not empty>
    - idToken.type must be DirectPayment
    - idToken.additionalInfo.additionalIdToken must be <Configured CardLast4Digits>
    - idToken.additionalInfo.type must be CardLast4Digits

* Step 4:
    Message TransactionEventResponse
    transactionLimit.maxCost = <not omitted>

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.9. Page 1038 - (2026-02) - TC_C_119_CSMS / TC_C_120_CSMS / TC_C_125_CSMS / TC_C_126_CSMS - Added
        missing triggerReason and stoppedReason
        | Test case Id | TC_C_119_CSMS / TC_C_120_CSMS / TC_C_125_CSMS / TC_C_126_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | X. The Test System sends a TransactionEventRequest with / eventType Ended / idToken.type
          DirectPayment / … / transactionInfo.stoppedReason Local / triggerReason StopAuthorized / … | 4. The
          CSMS responds with a TransactionEventResponse |
        | … | |
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from payment import fixed_fee_cost_details, new_psp_ref
from reusable_states.booted import booted
from trigger import kiosk_payment_authorized
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CARD_LAST_4_DIGITS = os.environ['CARD_LAST_4_DIGITS']

# The amount the payment terminal has authorized for the payment card
AUTHORIZATION_AMOUNT = 50.00


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_126(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: the Test System has AuthCtrlr.AuthorizeRemoteStart = false,
    # TariffCostCtrlr.Enabled[Cost] = true (the station calculates the cost locally) and
    # TariffCostCtrlr.Currency = "EUR".
    cp.variables = {
        'AuthCtrlr.AuthorizeRemoteStart': 'false',
        'TariffCostCtrlr.Enabled[Cost]': 'true',
        'TariffCostCtrlr.Currency': 'EUR',
    }
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Present a payment card to the payment terminal Kiosk for Charging
    #                Station with identity <Configured unique Charging Station identifier>
    # 1. The CSMS sends a RequestStartTransactionRequest
    # 2. The Test System responds with a RequestStartTransactionResponse with status Accepted
    request = await cp.wait_for_request(
        'RequestStartTransaction',
        manual_action=kiosk_payment_authorized(
            BASIC_AUTH_CP, psp_ref=new_psp_ref(), evse_id=CONFIGURED_EVSE_ID,
            card_last_4_digits=CARD_LAST_4_DIGITS, authorization_amount=AUTHORIZATION_AMOUNT))

    assert request.evse_id == CONFIGURED_EVSE_ID, \
        f"Expected RequestStartTransactionRequest.evseId {CONFIGURED_EVSE_ID}, got {request.evse_id}"
    assert request.remote_start_id is not None, "RequestStartTransactionRequest has no remoteStartId"
    assert request.id_token.id_token, "RequestStartTransactionRequest.idToken.idToken is empty"
    assert request.id_token.type == 'DirectPayment', \
        f"Expected idToken.type DirectPayment, got {request.id_token.type}"
    card_details = [info for info in request.id_token.additional_info or []
                    if info.type == 'CardLast4Digits']
    assert card_details, \
        f"Expected idToken.additionalInfo with type CardLast4Digits, got {request.id_token.additional_info}"
    assert card_details[0].additional_id_token == CARD_LAST_4_DIGITS, \
        f"Expected idToken.additionalInfo.additionalIdToken {CARD_LAST_4_DIGITS}, " \
        f"got {card_details[0].additional_id_token}"

    # 3. The Test System sends a TransactionEventRequest with
    #    - eventType Started
    #    - idToken <IdToken from step 1>
    #    - idToken.type DirectPayment
    #    - idToken.additionalInfo <additionalInfo>
    #    - transactionInfo.transactionId <transactionId>
    #    It is the first TransactionEventRequest after the RequestStartTransactionRequest, so it
    #    has triggerReason RemoteStart and the remoteStartId (F02.FR.21).
    # 4. The CSMS responds with a TransactionEventResponse
    transaction_id = cp.session.start_transaction()
    response = await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='RemoteStart',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'remote_start_id': request.remote_start_id},
        id_token=request.id_token,
    ))
    # transactionLimit.maxCost = <not omitted>
    assert response.transaction_limit is not None and response.transaction_limit.max_cost is not None, \
        f"TransactionEventResponse has no transactionLimit.maxCost: {response.transaction_limit}"
    max_cost = response.transaction_limit.max_cost

    # Settlement
    # 5. The Test System sends a TransactionEventRequest with
    #    - eventType Ended
    #    - idToken <IdToken from step 1>
    #    - idToken.type DirectPayment
    #    - transactionInfo.transactionId <transactionId>
    #    - transactionInfo.transactionLimit.maxCost <not omitted>
    #    - transactionInfo.stoppedReason Local and triggerReason StopAuthorized (errata 2026-09,
    #      6.3.9)
    #    - costDetails: a fixed fee of 15.00 EUR excluding and 18.15 EUR including tax (type
    #      MyTax, 21), totalUsage.energy 123, chargingTime 5, idleTime 0, chargingPeriods
    #      <omitted>
    # 6. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='StopAuthorized',
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'stopped_reason': 'Local',
            'transaction_limit': {'max_cost': max_cost},
        },
        id_token=request.id_token,
        cost_details=fixed_fee_cost_details(),
    ))

    # Note: The CSMS sends a message to Payment Kiosk or PSP to settle the cost for amount:
    # 18.15 EUR. That happens between the CSMS and the Payment Kiosk or PSP, where this test
    # cannot see it.

    start_task.cancel()
