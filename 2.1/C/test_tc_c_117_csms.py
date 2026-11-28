"""
Test case name      Settlement at end of transaction - settled by CSMS, receipt by CSMS
Test case Id        TC_C_117_CSMS
Use case Id(s)      C21
Requirement(s)      C21.FR.03, C21.FR.05

Requirement Details:
    C21.FR.03: CSMS SHALL respond with NotifySettlementResponse with receiptUrl.
        Precondition: C21.FR.02 AND PaymentCtrlr.ReceiptByCSMS = true
    C21.FR.05: CSMS SHALL settle the total cost of the transaction with the payment service provider.
        Precondition: When a locally started transaction ends that was authorized by an idToken of type =
                      DirectPayment AND PaymentCtrlr.SettlementByCSMS is true
        Note: The PSP reference to settle the payment session is in idToken.
System under test   CSMS

Description         Settle the amount of charging session via CSMS.

Purpose             To verify if the CSMS is able to settle a transaction directly via PSP.

Prerequisite(s)     - CSMS has an interface to the PSP. - CSMS supports Charging Stations with integrated
                      payment terminals.
                    - Test System has PaymentCtrlr.Enabled = true
                    - Test System has PaymentCtrlr.AuthorizeDirectPayment = false
                    - Test System has PaymentCtrlr.AuthorizeAmount = 50.00
                    - Test System has PaymentCtrlr.PaymentDetails = "CardLast4Digits"
                    - Test System has PaymentCtrlr.SettlementByCSMS = true
                    - Value of PaymentCtrlr.ReceiptByCSMS is irrelevant.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - eventType Started
    - idToken <PspRef>
    - idToken.type DirectPayment
    - transactionInfo.transactionId <transactionId>
    - idToken.additionalInfo[0].additionalIdToken = <not omitted>
    - idToken.additionalInfo[0].type = CardLast4Digits
    - transactionInfo.transactionLimit.maxCost 50.00
2. The CSMS responds with a TransactionEventResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - idToken <PspRef>
    - idToken.type DirectPayment
    - triggerReason StopAuthorized
    - transactionInfo.stoppedReason Local
    - transactionInfo.transactionId <transactionId>
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.fixed.exclTax 15.00
    - costDetails.totalCost.fixed.inclTax 18.15 EUR
    - costDetails.totalCost.fixed.taxRate.type MyTax
    - costDetails.totalCost.fixed.taxRate.tax 21
    - costDetails.totalUsage.energy 123
    - costDetails.totalUsage.chargingTime 5
    - costDetails.totalUsage.idleTime 0
    - costDetails.chargingPeriods <omitted>
4. The CSMS responds with a TransactionEventResponse

Note(s):
- The CSMS settles the total cost of the transaction with the payment service provider for amount of 18.15
  EUR.

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from payment import direct_payment_id_token, fixed_fee_cost_details, new_psp_ref, payment_ctrlr_variables
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_117(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: the Test System has PaymentCtrlr.Enabled = true, AuthorizeDirectPayment =
    # false, the authorization amount 50.00, PaymentDetails = "CardLast4Digits" and
    # SettlementByCSMS = true.
    cp.variables = payment_ctrlr_variables(settlement_by_csms=True)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    psp_ref = new_psp_ref()
    id_token = direct_payment_id_token(psp_ref)
    transaction_id = cp.session.start_transaction()

    # 1. The Test System sends a TransactionEventRequest with
    #    - eventType Started
    #    - idToken <PspRef>
    #    - idToken.type DirectPayment
    #    - transactionInfo.transactionId <transactionId>
    #    - idToken.additionalInfo[0].additionalIdToken = <not omitted>
    #    - idToken.additionalInfo[0].type = CardLast4Digits
    #    - transactionInfo.transactionLimit.maxCost 50.00
    # 2. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='Authorized',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'transaction_limit': {'max_cost': 50.00}},
        id_token=id_token,
    ))

    # 3. The Test System sends a TransactionEventRequest with
    #    - eventType Ended
    #    - idToken <PspRef>
    #    - idToken.type DirectPayment
    #    - triggerReason StopAuthorized
    #    - transactionInfo.stoppedReason Local
    #    - transactionInfo.transactionId <transactionId>
    #    - costDetails.totalCost.currency EUR
    #    - costDetails.totalCost.fixed.exclTax 15.00
    #    - costDetails.totalCost.fixed.inclTax 18.15 EUR
    #    - costDetails.totalCost.fixed.taxRate.type MyTax
    #    - costDetails.totalCost.fixed.taxRate.tax 21
    #    - costDetails.totalUsage.energy 123
    #    - costDetails.totalUsage.chargingTime 5
    #    - costDetails.totalUsage.idleTime 0
    #    - costDetails.chargingPeriods <omitted>
    # 4. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='StopAuthorized',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'stopped_reason': 'Local'},
        id_token=id_token,
        cost_details=fixed_fee_cost_details(),
    ))

    # Note: The CSMS settles the total cost of the transaction with the payment service
    # provider for amount of 18.15 EUR. That happens between the CSMS and the PSP, where this
    # test cannot see it.

    start_task.cancel()
