"""
Test case name      Integrated Payment Terminal - Cancelation after start of transaction - stopped by EV
                    driver
Test case Id        TC_C_113_CSMS
Use case Id(s)      C20
Requirement(s)      C20.FR.05

Requirement Details:
    C20.FR.05: Charging Station SHALL send a NotifySettlementRequest with transactiondId of transaction,
               idToken of the ad hoc payment in pspRef, and status = Canceled and settlementTime set to
               current time.
        Precondition: C20.FR.04
        Note: This notifies CSMS that the DirectPayment idToken has not been charged for the transaction.
System under test   CSMS

Description         To inform the CSMS that payment has been canceled and the authorization amount has been
                    released.

Purpose             To verify if the CSMS is able to handle Cancelation of a local payment terminal
                    authorization after a transaction has started when the EV driver stops the session at the
                    Charging Station.

Prerequisite(s)     - CSMS supports Charging Stations with integrated payment terminals.
                    - Test System has PaymentCtrlr.AuthorizeDirectPayment = false
                    - Test System has PaymentCtrlr.AuthorizationAmount = 50.00
                    - Test System has PaymentCtrlr.PaymentDetails = "CardLast4Digits"
                    - Test System has PaymentCtrlr.SettlementByCSMS = false

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Note: Starts and immediately ends a transaction

1. The Test System sends a TransactionEventRequest with
    - eventType Started
    - triggerReason Authorized
    - idToken <pspRef>
    - idToken.type DirectPayment
    - idToken.additionalInfo[0].additionalIdToken = 1234
    - idToken.additionalInfo[0].type = Last4Digits
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.transactionLimit.maxCost 50.00
2. The CSMS responds with a TransactionEventResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - idToken <pspRef>
    - idToken.type DirectPayment
    - idToken.additionalInfo[0].additionalIdToken = 1234
    - idToken.additionalInfo[0].type = Last4Digits
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.stoppedReason Local
    - triggerReason StopAuthorized
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.typeOfCost NormalCost
    - costDetails.totalCost.total 0
    - costDetails.totalUsage.energy 0
    - costDetails.totalUsage.chargingTime 0
    - costDetails.totalUsage.idleTime 0
4. The CSMS responds with a TransactionEventResponse
5. The Test System sends a NotifySettlementRequest with
    - transactionId <transactionId>
    - pspRef <pspRef>
    - status Canceled
    - settlementTime <Equal to timestamp step 3>
    - settlementAmount 0
    - receiptUrl <omitted>
6. The CSMS responds with a NotifySettlementResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os
import uuid

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

# Prerequisites: the Test System has PaymentCtrlr.AuthorizeDirectPayment = false,
# PaymentCtrlr.AuthorizationAmount = 50.00, PaymentCtrlr.PaymentDetails = "CardLast4Digits" and
# PaymentCtrlr.SettlementByCSMS = false.
AUTHORIZATION_AMOUNT = 50.00


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_113(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # The reference of the ad hoc payment at the payment service provider
    psp_ref = f"PSP-{uuid.uuid4()}"
    id_token = {
        'id_token': psp_ref,
        'type': 'DirectPayment',
        'additional_info': [{'additional_id_token': '1234', 'type': 'Last4Digits'}],
    }
    transaction_id = cp.session.start_transaction()

    # Note: Starts and immediately ends a transaction
    # 1. The Test System sends a TransactionEventRequest with
    #    - eventType Started
    #    - triggerReason Authorized
    #    - idToken <pspRef>
    #    - idToken.type DirectPayment
    #    - idToken.additionalInfo[0].additionalIdToken = 1234
    #    - idToken.additionalInfo[0].type = Last4Digits
    #    - transactionInfo.transactionId <transactionId>
    #    - transactionInfo.transactionLimit.maxCost 50.00
    # 2. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='Authorized',
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'transaction_limit': {'max_cost': AUTHORIZATION_AMOUNT},
        },
        id_token=id_token,
    ))

    # 3. The Test System sends a TransactionEventRequest with
    #    - eventType Ended
    #    - idToken <pspRef>, idToken.type DirectPayment, idToken.additionalInfo as in step 1
    #    - transactionInfo.transactionId <transactionId>
    #    - transactionInfo.stoppedReason Local
    #    - triggerReason StopAuthorized
    #    - costDetails.totalCost.currency EUR
    #    - costDetails.totalCost.typeOfCost NormalCost
    #    - costDetails.totalCost.total 0
    #    - costDetails.totalUsage.energy 0
    #    - costDetails.totalUsage.chargingTime 0
    #    - costDetails.totalUsage.idleTime 0
    # 4. The CSMS responds with a TransactionEventResponse
    ended_timestamp = utc_now_iso()
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=ended_timestamp,
        trigger_reason='StopAuthorized',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'stopped_reason': 'Local'},
        id_token=id_token,
        cost_details={
            'total_cost': {
                'currency': 'EUR',
                'type_of_cost': 'NormalCost',
                'total': {'excl_tax': 0, 'incl_tax': 0},
            },
            'total_usage': {'energy': 0, 'charging_time': 0, 'idle_time': 0},
        },
    ))

    # 5. The Test System sends a NotifySettlementRequest with
    #    - transactionId <transactionId>
    #    - pspRef <pspRef>
    #    - status Canceled
    #    - settlementTime <Equal to timestamp step 3>
    #    - settlementAmount 0
    #    - receiptUrl <omitted>
    # 6. The CSMS responds with a NotifySettlementResponse
    await cp.call(call.NotifySettlement(
        transaction_id=transaction_id,
        psp_ref=psp_ref,
        status='Canceled',
        settlement_time=ended_timestamp,
        settlement_amount=0,
    ))

    start_task.cancel()
