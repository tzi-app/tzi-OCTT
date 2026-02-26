"""
Test case name      Invalid ChargePointCertificate Security Event
Test case Id        TC_077_CSMS
Section             3.21.2 Security event/logging
System under test   Central System
Document reference  Table 189, page 162/176 (OCPP Compliancy Testing Tool - TestCaseDocument, 2025-11)

Description         The Charge Point notifies the Central System of an invalid certificate.

Purpose             To check if the Central System can handle when a Charge Point registers a security event and notifies the
                    Central System about it.

Prerequisite(s)     The Central System supports security profile 3.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1. The Central System sends an ExtendedTriggerMessage.req
    2. The Charge Point responds with an ExtendedTriggerMessage.conf

    [The Charge Point generates a new public/private key pair and generates a Certificate Signing Request.]
    3. The Charge Point sends a SignCertificate.req

    4. The Central System responds with a SignCertificate.conf

    [The Charge Point verifies the validity of the signed certificate.]
    5. The Central System sends a CertificateSigned.req

    6. The Charge Point responds with a CertificateSigned.conf

    7. The Charge Point sends a SecurityEventNotification.req
    8. The Central System responds with a SecurityEventNotification.conf

Tool Validations
    * Step 1:
        (Message: ExtendedTriggerMessage.req)
        The requestedMessage is SignChargePointCertificate
        The connectorId is <Omitted>

    * Step 2:
        (Message: ExtendedTriggerMessage.conf)
        The status is Accepted

    * Step 4:
        (Message: SignCertificate.conf)
        The status is Accepted

    * Step 5:
        (Message: CertificateSigned.req)
        The certificate is <Signed ChargePointCertificate>

    * Step 6:
        (Message: CertificateSigned.conf)
        The status is Rejected

    * Step 7:
        (Message: SecurityEventNotification.req)
        The type is InvalidChargePointCertificate

Expected result(s) / behaviour: n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import CertificateSignedStatus, GenericStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_077(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)

    # Set CertificateSigned response to Rejected before starting
    cp._certificate_signed_response_status = CertificateSignedStatus.rejected

    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ExtendedTriggerMessage.req
    await asyncio.wait_for(cp._received_extended_trigger.wait(), timeout=ACTION_TIMEOUT)
    assert cp._extended_trigger_requested == 'SignChargePointCertificate'

    # Step 3-4: CP sends SignCertificate.req
    sign_response = await cp.send_sign_certificate(csr='dummy-csr')
    assert sign_response.status == GenericStatus.accepted

    # Step 5-6: Wait for CSMS to send CertificateSigned.req, CP responds Rejected
    await asyncio.wait_for(cp._received_certificate_signed.wait(), timeout=ACTION_TIMEOUT)
    assert cp._certificate_signed_chain is not None

    # Step 7-8: CP sends SecurityEventNotification for invalid certificate
    await cp.send_security_event_notification('InvalidChargePointCertificate')

    start_task.cancel()
