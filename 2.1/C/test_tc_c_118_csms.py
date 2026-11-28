"""
Test case name      Settlement at end of transaction - settled by CS, receipt by CSMS
Test case Id        TC_C_118_CSMS
Use case Id(s)      C21
Requirement(s)      C21.FR.03

Requirement Details:
    C21.FR.03: CSMS SHALL respond with NotifySettlementResponse with receiptUrl.
        Precondition: C21.FR.02 AND PaymentCtrlr.ReceiptByCSMS = true
System under test   CSMS

Description         In order to test that Charging Station supports settlement at the end of a transaction
                    where the settlement is handled by the Charging Station and the receipt is provided by the
                    CSMS.

Purpose             To verify that the CSMS can properly handle a transaction where the settlement is done by
                    the Charging Station and the CSMS provides the receipt.

Prerequisite(s)     - CSMS supports settlement at the end of a transaction. - CSMS supports Charging Stations
                      with integrated payment terminals.
                    - Test System has PaymentCtrlr.Enabled = true
                    - Test System has PaymentCtrlr.AuthorizeDirectPayment = false
                    - Test System has PaymentCtrlr.AuthorizationAmount = 50.00
                    - Test System has PaymentCtrlr.PaymentDetails = "CardLast4Digits"
                    - Test System has PaymentCtrlr.SettlementByCSMS = false
                    - Test System has PaymentCtrlr.ReceiptByCSMS = true
                    - CSMS lets the CS handle the settlement at the end of a transaction, but the CSMS
                      provides receipts.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - eventType Started
    - idToken <configured PspRef>
    - idToken.type DirectPayment
    - transactionInfo.transactionId <transactionId>
    - idToken.additionalInfo[0].additionalIdToken = <not omitted>
    - idToken.additionalInfo[0].type = CardLast4Digits
    - transactionInfo.transactionLimit.maxCost 50.00
2. The CSMS responds with a TransactionEventResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - triggerReason StopAuthorized
    - idToken <configured PspRef>
    - idToken.type DirectPayment
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.stoppedReason Local
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.fixed.exclTax 15.00
    - costDetails.totalCost.fixed.inclTax 18.15 EUR
    - costDetails.totalCost.fixed.taxRate.type MyTax
    - costDetails.totalCost.fixed.taxRate.tax 21
    - costDetails.totalUsage.energy 123
    - costDetails.totalUsage.chargingTime 5
    - costDetails.totalUsage.idleTime 0
    - costDetails.chargingPeriods[ <omitted>
4. The CSMS responds with a TransactionEventResponse
5. The Test System sends a NotifySettlementRequest with
    - transactionId <transactionId>
    - pspRef <configured PspRef>
    - status Settled
    - settlementTime <not omitted>
    - settlementAmount 18.15
    - receiptUrl <omitted>
6. The CSMS responds with a NotifySettlementResponse

Tool validations
* Step 6:
    Message NotifySettlementResponse
    - receiptUrl must be <not omitted>

Post scenario validations:
    - Verify that the receipt URL provided by the CSMS is valid and accessible.
"""

import asyncio
import os
import urllib.request
from urllib.parse import urlparse

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from payment import direct_payment_id_token, fixed_fee_cost_details, new_psp_ref, payment_ctrlr_variables
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


def _fetch_status(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_118(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: the Test System has PaymentCtrlr.Enabled = true, AuthorizeDirectPayment =
    # false, AuthorizationAmount = 50.00, PaymentDetails = "CardLast4Digits", SettlementByCSMS
    # = false and ReceiptByCSMS = true.
    cp.variables = payment_ctrlr_variables(settlement_by_csms=False, receipt_by_csms=True)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    psp_ref = new_psp_ref()
    id_token = direct_payment_id_token(psp_ref)
    transaction_id = cp.session.start_transaction()

    # 1. The Test System sends a TransactionEventRequest with
    #    - eventType Started
    #    - idToken <configured PspRef>
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
    #    - triggerReason StopAuthorized
    #    - idToken <configured PspRef>
    #    - idToken.type DirectPayment
    #    - transactionInfo.transactionId <transactionId>
    #    - transactionInfo.stoppedReason Local
    #    - costDetails: a fixed fee of 15.00 EUR excluding and 18.15 EUR including tax (type
    #      MyTax, 21), totalUsage.energy 123, chargingTime 5, idleTime 0, chargingPeriods
    #      <omitted>
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

    # 5. The Test System sends a NotifySettlementRequest with
    #    - transactionId <transactionId>
    #    - pspRef <configured PspRef>
    #    - status Settled
    #    - settlementTime <not omitted>
    #    - settlementAmount 18.15
    #    - receiptUrl <omitted>
    # 6. The CSMS responds with a NotifySettlementResponse
    response = await cp.call(call.NotifySettlement(
        transaction_id=transaction_id,
        psp_ref=psp_ref,
        status='Settled',
        settlement_time=utc_now_iso(),
        settlement_amount=18.15,
    ))

    # receiptUrl must be <not omitted>
    assert response.receipt_url, "NotifySettlementResponse has no receiptUrl"
    # Verify that the receipt URL provided by the CSMS is valid and accessible.
    url = urlparse(response.receipt_url)
    assert url.scheme in ('http', 'https') and url.netloc, \
        f"NotifySettlementResponse.receiptUrl is not a valid URL: {response.receipt_url}"
    try:
        status = await asyncio.get_running_loop().run_in_executor(None, _fetch_status, response.receipt_url)
    except Exception as error:
        pytest.fail(f"The receipt URL {response.receipt_url} is not accessible: {error!r}")
    assert 200 <= status < 300, \
        f"The receipt URL {response.receipt_url} is not accessible: HTTP {status}"

    start_task.cancel()
