"""
Test case name      Install CA certificate - Failed
Test case Id        TC_M_05_CSMS
Use case Id(s)      M05
Requirement(s)      M05.FR.01, M05.FR.03

Requirement Details:
    M05.FR.01: The Charging Station SHALL attempt to install the certificate and respond with an
               InstallCertificateResponse.
        Precondition: After receiving an InstallCertificateRequest
    M05.FR.03: The Charging Station SHALL indicate failure by setting status to Failed in the
               InstallCertificateResponse.
        Precondition: M05.FR.01 AND The installation failed
System under test   CSMS

Description         The CSMS is able to request the Charging Station to install new Root CA certificates using
                    the InstallCertificateRequest message.

Purpose             To verify if the CSMS is able to handle a Charging Station reporting it failed to install
                    the requested certificate.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send an InstallCertificateRequest with certificateType CSMSRootCertificate.

1. The CSMS sends a InstallCertificateRequest
2. The Test System responds with a InstallCertificateResponse
    With status is Failed

Tool validations
* Step 1:
    Message: InstallCertificateRequest
    certificateType must be CSMSRootCertificate
    certificate contains <A certificate>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from certificates import configured_certificate, is_certificate
from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_m_05(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger the CSMS to send an InstallCertificateRequest with certificateType
    #                CSMSRootCertificate.
    # 1. The CSMS sends a InstallCertificateRequest
    # 2. The Test System responds with a InstallCertificateResponse With status is Failed
    cp.set_response('InstallCertificate', status='Failed')
    request = await cp.wait_for_request(
        'InstallCertificate',
        manual_action=send_call(BASIC_AUTH_CP, 'InstallCertificate', {
            'certificateType': 'CSMSRootCertificate',
            'certificate': configured_certificate('CSMSRootCertificate'),
        }))
    assert request.certificate_type == 'CSMSRootCertificate', \
        f"Expected InstallCertificateRequest.certificateType CSMSRootCertificate, " \
        f"got {request.certificate_type}"
    # certificate contains <A certificate>
    assert is_certificate(request.certificate), \
        f"InstallCertificateRequest.certificate is not a PEM encoded certificate: {request.certificate}"

    start_task.cancel()
