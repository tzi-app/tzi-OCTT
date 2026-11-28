"""
Test case name      Settlement - is rejected or fails - Rejected
Test case Id        TC_C_120_CSMS
Use case Id(s)      C22
Requirement(s)      …
System under test   CSMS

Description         To inform the CSMS that the transaction settlement has been rejected or otherwise failed
                    to be successfully settled.

Purpose             To verify if the CSMS is able to handle if the settlement is rejected according the
                    Charging Station.

Prerequisite(s)     - CSMS supports Charging Stations with integrated payment terminals. - Test System has
                      PaymentCtrlr.Enabled is true
                    - Test System has PaymentCtrlr.AuthorizationAmount = 50.00
                    - Test System has PaymentCtrlr.PaymentDetails = "CardLast4Digits"
                    - Test System has PaymentCtrlr.SettlementByCSMS is false
                    - Test System has PaymentCtrlr.ReceiptByCSMS is false
                    - Test System has PaymentCtrlr.AuthorizeDirectPayment is false

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
    - idToken <configured PspRef>
    - idToken.type DirectPayment
    - transactionInfo.transactionId <transactionId>
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.fixed.exclTax 15.00
    - costDetails.totalCost.fixed.inclTax 18.15 EUR
    - costDetails.totalCost.fixed.taxRate.type MyTax
    - costDetails.totalCost.fixed.taxRate.tax 21
    - costDetails.totalUsage.energy 123
    - costDetails.totalUsage.chargingTime 5
    - costDetails.totalUsage.idleTime 0
    - costDetails.chargingPeriods is <omitted>
4. The CSMS responds with a TransactionEventResponse
5. The Test System sends a NotifySettlementRequest with
    - transactionId <transactionId>
    - pspRef <configured PspRef>
    - status Rejected
    - settlementTime <not omitted>
    - settlementAmount 18.15
    - receiptUrl <omitted>
6. The CSMS responds with a NotifySettlementResponse

Tool validations
N/a

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.11. Page 140 - (2026-06) - C22.FR.01/02 - clarify "without receipt information" [1286]
        (Part 2 errata - applies to this test via use case C22)
        Requirements C22.FR.01/02 mention that when settlement fails or is rejected, that Charging Station
        sends a NotifySettlementRequest without receipt information. C21.FR.03, however, always requires a
        receiptUrl, either from Charging Station or CSMS.

        The intention of C22.FR.01/02 is that the receipt is not a real receipt because there was no
        settlement. It is, however, allowed to provide a receiptUrl that points to a page that tells that the
        settlement has failed of was rejected. This is clarified by the following change of wording.

        Changed requirements

        | | ID | Precondition | Requirements | Note |
        | Old | C22.FR.01 | When Charging Station receives a settlement status from payment terminal that is
          Rejected | Charging Station SHALL send a [notifysettlementrequest] to CSMS with status = Rejected,
          settlementAmount, settlementTime, transactionId and pspRef without receipt information. | This means
          the payment service provider has rejected the settlement. |

        | | ID | Precondition | Requirements | Note |
        | New | C22.FR.01 | When Charging Station receives a settlement status from payment terminal that is
          Rejected | Charging Station SHALL send a [notifysettlementrequest] to CSMS with status = Rejected,
          settlementAmount, settlementTime, transactionId, pspRef and a receiptUrl for a rejected settlement.
          | This means the payment service provider has rejected the settlement. Information about this may be
          provided in receiptUrl |
        | Old | C22.FR.02 | When Charging Station receives a settlement status from payment terminal that is
          Failed | Charging Station SHALL send a [notifysettlementrequest] to CSMS with status = Failed,
          settlementAmount, settlementTime, transactionId and pspRef without receipt information. | This means
          that there are technical reasons why the settlement failed, e.g. a failure to communicate. |
        | New | C22.FR.02 | When Charging Station receives a settlement status from payment terminal that is
          Failed | Charging Station SHALL send a [notifysettlementrequest] to CSMS with status = Failed,
          settlementAmount, settlementTime, transactionId, pspRef and a receiptUrl for a failed settlement. |
          This means that there are technical reasons why the settlement failed, e.g. a failure to
          communicate. Information about this may be provided in receiptUrl |

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
from payment import direct_payment_id_token, fixed_fee_cost_details, new_psp_ref, payment_ctrlr_variables
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_120(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: the Test System has PaymentCtrlr.Enabled is true, AuthorizationAmount =
    # 50.00, PaymentDetails = "CardLast4Digits", SettlementByCSMS is false, ReceiptByCSMS is
    # false and AuthorizeDirectPayment is false.
    cp.variables = payment_ctrlr_variables(settlement_by_csms=False, receipt_by_csms=False)
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
    #    - idToken <configured PspRef>
    #    - idToken.type DirectPayment
    #    - transactionInfo.transactionId <transactionId>
    #    - transactionInfo.stoppedReason Local and triggerReason StopAuthorized (errata 2026-09,
    #      6.3.9)
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
    #    - status Rejected
    #    - settlementTime <not omitted>
    #    - settlementAmount 18.15
    #    - receiptUrl <omitted>
    # 6. The CSMS responds with a NotifySettlementResponse
    await cp.call(call.NotifySettlement(
        transaction_id=transaction_id,
        psp_ref=psp_ref,
        status='Rejected',
        settlement_time=utc_now_iso(),
        settlement_amount=18.15,
    ))

    start_task.cancel()
