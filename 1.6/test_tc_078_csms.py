"""
Test case name      Invalid CentralSystemCertificate Security Event
Test case Id        TC_078_CSMS
Table               190 (page 163/176 of CompliancyTestTool-TestCaseDocument)
Section             3.21.2 Security event/logging
System under test   Central System

Description         The Charge Point notifies the Central System of an invalid certificate.

Purpose             To check if the Central System can handle it when a Charge Point registers a security event and notifies the
                    Central System about it.

Prerequisite(s)     The Central System supports Security profile 2 and/or 3.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1. The Central System sends an InstallCertificate.req
    2. The Charge Point responds with an InstallCertificate.conf

    3. The Charge Point sends a SecurityEventNotification.req
    4. The Central System responds with a SecurityEventNotification.conf

Tool Validations
    * Step 1:
        (Message: InstallCertificate.req)
        certificateType is CentralSystemRootCertificate
        certificate is <Configured certificate>

        Note: For this testcase the OCTT will reject any certificate.

    * Step 2:
        (Message: InstallCertificate.conf)
        status is Rejected

    * Step 3:
        (Message: SecurityEventNotification.req)
        The type is InvalidCentralSystemCertificate

Expected result(s) / behaviour: n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import CertificateStatus

from charge_point import TziChargePoint16
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_078(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)

    # Set InstallCertificate response to Rejected before starting
    cp._install_certificate_response_status = CertificateStatus.rejected

    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send InstallCertificate.req, CP responds Rejected
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'install-certificate', {
        'certificateType': 'CentralSystemRootCertificate',
        'certificate': '-----BEGIN CERTIFICATE-----\nMIIBkTCB+wIUEjRWeJQ=\n-----END CERTIFICATE-----',
    }))
    await asyncio.wait_for(cp._received_install_certificate.wait(), timeout=ACTION_TIMEOUT)
    assert cp._install_certificate_data['certificate_type'] == 'CentralSystemRootCertificate'

    # Step 3-4: CP sends SecurityEventNotification for invalid CS certificate
    await cp.send_security_event_notification('InvalidCentralSystemCertificate')

    start_task.cancel()
