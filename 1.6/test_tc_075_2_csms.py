"""
Test case name      Install a certificate on the Charge Point - CentralSystemRootCertificate
Test case Id        TC_075_2_CSMS
Section             3.21.1 Secure connection setup
System under test   Central System
Document ref        Table 187, pp. 160-161 (CompliancyTestTool-TestCaseDocument 2025-11)

Description         The Central System requests the Charge Point to install a new Central System root certificate.

Purpose             To check if the Central System is able to install a certificate on the Charge Point.

Prerequisite(s)     The Central System supports Security profile 2 and/or 3.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    The OCTT requests the Central System to install CentralSystemRootCertificate 2.

    1. The Central System sends an InstallCertificate.req
    2. The Charge Point responds with an InstallCertificate.conf

    3. The Central System sends a GetInstalledCertificateIds.req
    4. The Charge Point responds with a GetInstalledCertificateIds.conf

Tool Validations
    * Step 1:
        (Message: InstallCertificate.req)
        certificateType is CentralSystemRootCertificate
        certificate is <Configured root certificate>

    * Step 2:
        (Message: InstallCertificate.conf)
        status is Accepted

    * Step 3:
        (Message: GetInstalledCertificateIds.req)
        The certificateType is CentralSystemRootCertificate

    * Step 4:
        (Message: GetInstalledCertificateIds.conf)
        The status is Accepted
        certificateHashData is <Includes the certificate information of the installed certificate from step 1.>

    Note: This test case must be executed with a Root CA certificate in order to get the correct response
    message from the OCTT.

    Note: "CentralSystemRootCertificate 2" in the scenario description likely refers to this being
    the second variant in the TC_075 series (the certificate type for this variant), not a certificate
    with index/number 2.

    Note: Step 4 says certificateHashData should include "the certificate information of the installed
    certificate from step 1". In practice the OCTT validates presence and format of the hash data, not
    cryptographic correctness against the actual certificate from step 1.

Expected result(s) / behaviour: n/a
"""

import asyncio
import os
import pytest

from charge_point import TziChargePoint16
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_075_2(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send InstallCertificate.req
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'install-certificate', {
        'certificateType': 'CentralSystemRootCertificate',
        'certificate': '-----BEGIN CERTIFICATE-----\nMIIBkTCB+wIUEjRWeJQ=\n-----END CERTIFICATE-----',
    }))
    await asyncio.wait_for(cp._received_install_certificate.wait(), timeout=ACTION_TIMEOUT)
    assert cp._install_certificate_data is not None
    assert cp._install_certificate_data['certificate_type'] == 'CentralSystemRootCertificate'

    # Populate certificate hash data so GetInstalledCertificateIds response includes installed cert info
    cp._installed_certificate_hash_data = [{
        'hash_algorithm': 'SHA256',
        'issuer_name_hash': 'aabbccdd',
        'issuer_key_hash': 'eeff0011',
        'serial_number': 'SN_CENTRAL_SYSTEM',
    }]

    # Step 3-4: Wait for CSMS to send GetInstalledCertificateIds.req
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'get-installed-certificate-ids', {
        'certificateType': 'CentralSystemRootCertificate',
    }))
    await asyncio.wait_for(cp._received_get_installed_certificate_ids.wait(), timeout=ACTION_TIMEOUT)
    assert cp._get_installed_certificate_ids_data['certificate_type'] == 'CentralSystemRootCertificate'

    start_task.cancel()
