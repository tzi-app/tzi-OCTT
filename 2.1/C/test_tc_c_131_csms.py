"""
Test case name      Ad hoc payment via static or dynamic QR code - success
Test case Id        TC_C_131_CSMS
Use case Id(s)      C25
Requirement(s)      C25.FR.07, C25.FR.09, C25.FR.20, C25.FR.21, C25.FR.23, C25.FR.24, C25.FR.40, C25.FR.41

Requirement Details:
    C25.FR.07: CSMS SHALL validate the time-based one-time password in the URL
        Precondition: When EV Driver visits the web page of CSMS using the URL in the QR code
        Note: See description in Validation of TOTP.
    C25.FR.09: CSMS SHALL decode the URL parameters as defined in URL definition for dynamic QR code.
        Precondition: If the time-based one-time password in the URL is valid
        Note: URL parameters must at least include an identity of the Charging Station and optionally an EVSE
              number.
    C25.FR.20: CSMS SHALL forward EV Driver to a web page of PSP to enter payment credentials
        Precondition: If URL successfully decoded
        Note: The protocol between PSP and CSMS is not specified in this document.
    C25.FR.21: CSMS MAY send a NotifyWebPaymentStartedRequest message with evseId having the EVSE number that
               was decoded from the URL and timeout the time in seconds that Charging Station may lock the
               EVSE to prevent locally started transactions.
        Precondition: C25.FR.20
        Note: After timeout seconds Charging Station should free the EVSE again for local transactions.
    C25.FR.23: CSMS SHALL send a RequestStartTransactionRequest to Charging Station with identity <CS> and
               EVSE <evse> (when present) and having idToken.idToken = <PspRef> and idToken.type =
               DirectPayment
        Precondition: When CSMS receives a message from Payment Kiosk that payment is authorized with
                      authorization reference <PspRef> for Charging Station with identity <CS> and optionally
                      an EVSE <evse>
        Note: There is need to include additionalInfo elements for payment details, like cardBin,
              cardLast4Digits, towards Charging Station. The protocol between Payment Kiosk and CSMS is not
              specified in this document.
    C25.FR.24: CSMS SHALL respond with a TransactionEventResponse with transactionLimit set to the required
               limit.
        Precondition: C25.FR.23 AND Charging Station sends a TransactionEventRequest with eventType = Started
        Note: transactionLimit uses maxCost for cost limit, maxEnergy for energy limit, maxTime for time limit
              or maxSoC for SoC limit.
    C25.FR.40: CSMS SHALL send a message to PSP to settle the cost
        Precondition: After CSMS received a TransactionEventRequest with eventType = Ended or the transaction
        Note: Cost may have been calculated locally or centrally.
    C25.FR.41: CSMS MAY send a SetDisplayMessageRequest with a URL where EV Driver can download the receipt .
        Precondition: When CSMS receives receipt information or a URL to a receipt from PSP
        Note: Other methods to find and download receipts may also be offered by CSO.
System under test   CSMS

Description         In order to test that CSMS supports QR codes

Purpose             To verify if the CSMS is able to respond correctly when a QR code is scanned on Charging
                    Station

Prerequisite(s)     - CSMS configured for central cost calculation
                    - CSMS supports payments using dynamic QR codes
                    - CSMS supports url templates for QR code payments containing at least placeholders
                      {chargingstationid} and {totp}
                    Test System has:
                    - WebPaymentsCtrlr.Enabled is true
                    - WebPaymentsCtrlr.URLTemplate is <base-url>/{chargingstationid}/{evse}/{totp}/{version}
                    - WebPaymentsCtrlr.ValidityTime is 30
                    - WebPaymentsCtrlr.SharedSecret is mysharedsecret
                    - WebPaymentsCtrlr.Length is 8
                    - WebPaymentsCtrlr.TOTPVersion is 1

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Trigger CSMS to perform a payment and start a transaction via QR code webpage
    maxenergy is 20000
    qrUrl is <Configured QR base url> extended with:
    {chargingstationId} is <configured charging station id>
    {totp} is <valid totp>
    {evseId} is <configured evse>
    {version} is 1

1. The CSMS sends a RequestStartTransactionRequest
2. The Test System responds with RequestStartTransactionResponse with
    - status Accepted
3. The Test System sends a TransactionEventRequest with
    - eventType Started
    - triggerReason RemoteStart
    - idToken.idToken <PspRef>
    - idToken.type DirectPayment
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.remoteStartId <remoteStartId>
    - meterValue[0].timestamp <not omitted>
    - meterValue[0].sampledValue[0].value 10000
    - meterValue[0].sampledValue[0].context Transaction.Begin
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message RequestStartTransactionRequest
    - idToken.idToken must be <PspRef>
    - idToken.type must be DirectPayment
* Step 4:
    Message TransactionEventResponse
    - idTokenInfo.status must be Accepted
    - transactionLimit.maxEnergy must be 20000

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.10. Page 1046/1047 - (2026-02) - TC_C_131_CSMS - Use idToken from the RequestStartTransactionRequest,
        which contains the PspRef
        | Test case name | Ad hoc payment via static or dynamic QR code - success |
        | Test case Id | TC_C_131_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | 3. The Test System sends a TransactionEventRequest with / eventType Started / triggerReason
          RemoteStart / idToken.idToken [removed: <PspRef>] <idToken.idToken from step 1> / [removed:
          idToken.idToken] / idToken.type DirectPayment / transactionInfo.transactionId <transactionId> /
          transactionInfo.remoteStartId <remoteStartId> / meterValue[0].timestamp <not omitted> /
          meterValue[0].sampledValue[0].value 10000 / meterValue[0].sampledValue[0].context Transaction.Begin
          | 4. The CSMS responds with a TransactionEventResponse |
        | … | |

        | Tool validations |
        | \\* Step 1: / Message RequestStartTransactionRequest / idToken.idToken must [removed: be <PspRef>]
          NOT be omitted / … |

    6.3.11. Page 1046/1048/1049 - (2026-02) - TC_C_131_CSMS/TC_C_132_CSMS/TC_C_133_CSMS - Sharedsecret
        configuration variable added
        The hardcoded value used for WebPaymentsCtrlr.SharedSecret ("mysharedsecret") has been replaced with a
        configurable variable <Configured sharedsecret>.
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from payment import qr_code_url, totp_v1, web_payments_ctrlr_variables
from reusable_states.booted import booted
from trigger import qr_code_payment
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
# WebPaymentsCtrlr.SharedSecret: <Configured sharedsecret> (errata 2026-09, 6.3.11)
QR_CODE_SHARED_SECRET = os.environ['QR_CODE_SHARED_SECRET']

MAX_ENERGY = 20000


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_131(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: the Test System has WebPaymentsCtrlr.Enabled true, URLTemplate
    # <base-url>/{chargingstationid}/{evse}/{totp}/{version}, ValidityTime 30, Length 8 and
    # TOTPVersion 1.
    cp.variables = web_payments_ctrlr_variables()
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger CSMS to perform a payment and start a transaction via QR code
    #                webpage
    #     maxenergy is 20000
    #     qrUrl is <Configured QR base url> extended with:
    #     {chargingstationId} is <configured charging station id>
    #     {totp} is <valid totp>
    #     {evseId} is <configured evse>
    #     {version} is 1
    # 1. The CSMS sends a RequestStartTransactionRequest
    # 2. The Test System responds with RequestStartTransactionResponse with status Accepted
    qr_url = qr_code_url(BASIC_AUTH_CP, CONFIGURED_EVSE_ID, totp_v1(QR_CODE_SHARED_SECRET),
                         max_energy=MAX_ENERGY)
    request = await cp.wait_for_request(
        'RequestStartTransaction', manual_action=qr_code_payment(qr_url))

    # idToken.idToken must NOT be omitted (errata 2026-09, 6.3.10): it contains the PspRef
    assert request.id_token.id_token, "RequestStartTransactionRequest.idToken.idToken is empty"
    assert request.id_token.type == 'DirectPayment', \
        f"Expected idToken.type DirectPayment, got {request.id_token.type}"

    # 3. The Test System sends a TransactionEventRequest with
    #    - eventType Started
    #    - triggerReason RemoteStart
    #    - idToken.idToken <idToken.idToken from step 1>
    #    - idToken.type DirectPayment
    #    - transactionInfo.transactionId <transactionId>
    #    - transactionInfo.remoteStartId <remoteStartId>
    #    - meterValue[0].timestamp <not omitted>
    #    - meterValue[0].sampledValue[0].value 10000
    #    - meterValue[0].sampledValue[0].context Transaction.Begin
    # 4. The CSMS responds with a TransactionEventResponse
    transaction_id = cp.session.start_transaction()
    response = await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='RemoteStart',
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'remote_start_id': request.remote_start_id,
        },
        id_token={'id_token': request.id_token.id_token, 'type': 'DirectPayment'},
        meter_value=[{
            'timestamp': utc_now_iso(),
            'sampled_value': [{'value': 10000, 'context': 'Transaction.Begin'}],
        }],
    ))
    validate_id_token_info('TransactionEventResponse', response.id_token_info, status='Accepted')
    assert response.transaction_limit is not None \
        and response.transaction_limit.max_energy == MAX_ENERGY, \
        f"Expected TransactionEventResponse.transactionLimit.maxEnergy {MAX_ENERGY}, " \
        f"got {response.transaction_limit}"

    start_task.cancel()
