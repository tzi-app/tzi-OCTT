"""
Test case name      Ad hoc payment via static or dynamic QR code - invalid URL parameters
Test case Id        TC_C_132_CSMS
Use case Id(s)      C25
Requirement(s)      C25.FR.09

Requirement Details:
    C25.FR.09: CSMS SHALL decode the URL parameters as defined in URL definition for dynamic QR code.
        Precondition: If the time-based one-time password in the URL is valid
        Note: URL parameters must at least include an identity of the Charging Station and optionally an EVSE
              number.
System under test   CSMS

Description         In order to test that CSMS supports QR codes

Purpose             To verify if the CSMS is able to respond correctly when receiving invalid parameters.

Prerequisite(s)     - CSMS configured for central cost calculation
                    - CSMS supports payments using dynamic QR codes
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
{chargingstationId} is <omitted>
{totp} is <valid totp>
{evseId} is <configured evse>
{version} is 1

1. The CSMS does NOT send a RequestStartTransactionRequest

Tool validations
N/a

Post scenario validations:
    - CSMS detects that not all path parameters from URLTemplate are present and shows a web page that QR code
      is not valid.
    - CSMS doesn’t forward EV Driver to a web page of PSP to enter payment credentials and SHALL NOT authorize
      EV Driver to charge due missing chargingstationid URL parameter.

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.11. Page 1046/1048/1049 - (2026-02) - TC_C_131_CSMS/TC_C_132_CSMS/TC_C_133_CSMS - Sharedsecret
        configuration variable added
        The hardcoded value used for WebPaymentsCtrlr.SharedSecret ("mysharedsecret") has been replaced with a
        configurable variable <Configured sharedsecret>.
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
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
async def test_tc_c_132(connection):
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
    #     {chargingstationId} is <omitted>
    #     {totp} is <valid totp>
    #     {evseId} is <configured evse>
    #     {version} is 1
    # 1. The CSMS does NOT send a RequestStartTransactionRequest
    #    The CSMS detects that not all path parameters from URLTemplate are present. It does
    #    not forward the EV Driver to the PSP, and does not authorize the EV Driver to charge.
    qr_url = qr_code_url(None, CONFIGURED_EVSE_ID, totp_v1(QR_CODE_SHARED_SECRET),
                         max_energy=MAX_ENERGY)
    await cp.expect_no_request('RequestStartTransaction', manual_action=qr_code_payment(qr_url))

    start_task.cancel()
