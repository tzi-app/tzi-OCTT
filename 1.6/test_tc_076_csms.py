"""
Test case name      Delete a specific certificate from the Charge Point
Test case Id        TC_076_CSMS
Section             3.21.1 Secure connection setup
Reference           Table 188, pages 160-161 (CompliancyTestTool-TestCaseDocument 2025-11)
System under test   Central System

Description         To facilitate the management of the Charge Point's installed certificates, a method of deleting an installed
                    certificate is provided. The Central System requests the Charge Point to delete a specific certificate.

Purpose             To check if the Central System is able to delete an installed certificate from the Charge Point.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    The OCTT requests the Central System to install CentralSystemRootCertificate 2.

    1. The Central System sends an InstallCertificate.req
    2. The Charge Point responds with an InstallCertificate.conf

    The OCTT requests the Central System to delete the just installed CentralSystemRootCertificate 2.

    3. The Central System sends a GetInstalledCertificateIds.req
    4. The Charge Point responds with a GetInstalledCertificateIds.conf

        Note(s): The Central System sends a GetInstalledCertificateIds.req to confirm the hashAlgorithm
        it needs to use for requesting the deletion of the Root certificate.

    5. The Central System sends a DeleteCertificate.req
    6. The Charge Point responds with a DeleteCertificate.conf

    7. The Central System optionally sends a GetInstalledCertificateIds.req
    8. The Charge Point responds with a GetInstalledCertificateIds.conf

        Note(s): This step is optional. It is only used for the Central System to confirm the Root
        certificate actually has been deleted.

    Note(s):
    - Steps 1 - 8 will be repeated for each hash algorithm (SHA256, SHA384, SHA512).

Tool Validations
    * Step 4:
        (Message: GetInstalledCertificateIds.conf)
        status is Accepted
        certificateHashData.hashAlgorithm is <For each hash algorithm; (SHA256, SHA384, SHA512)>

    * Step 5:
        (Message: DeleteCertificate.req)
        hashAlgorithm is <Configured HashAlgorithm> (It needs to be equal to the hashAlgorithm returned at step 4)
        certificateHashData is <Includes the certificate information of the installed CentralSystemRootCertificate.>
        The individual fields of the certificateHashData are verified by the OCTT (the OCTT compares these with
        its own certificateHashData calculation).

    * Step 6:
        (Message: DeleteCertificate.conf)
        status is Accepted

Expected result(s) / behaviour: n/a
"""

import asyncio
import os
import pytest

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_076(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Steps 1-8 repeated for each hash algorithm (SHA256, SHA384, SHA512)
    hash_algorithms = ['SHA256', 'SHA384', 'SHA512']

    for iteration, hash_algo in enumerate(hash_algorithms):
        # Step 1-2: Wait for CSMS to send InstallCertificate.req
        if iteration > 0:
            cp._received_install_certificate.clear()
        await asyncio.wait_for(cp._received_install_certificate.wait(), timeout=ACTION_TIMEOUT)
        assert cp._install_certificate_data is not None

        # Prepare hash data response for GetInstalledCertificateIds
        cp._installed_certificate_hash_data = [{
            'hash_algorithm': hash_algo,
            'issuer_name_hash': 'aabbccdd',
            'issuer_key_hash': 'eeff0011',
            'serial_number': f'SN{iteration}',
        }]

        # Step 3-4: Wait for CSMS to send GetInstalledCertificateIds.req
        cp._received_get_installed_certificate_ids.clear()
        await asyncio.wait_for(cp._received_get_installed_certificate_ids.wait(), timeout=ACTION_TIMEOUT)

        # Step 5-6: Wait for CSMS to send DeleteCertificate.req
        cp._received_delete_certificate.clear()
        await asyncio.wait_for(cp._received_delete_certificate.wait(), timeout=ACTION_TIMEOUT)
        assert cp._delete_certificate_data is not None
        # Validate hash algorithm matches what we reported
        assert cp._delete_certificate_data.get('hash_algorithm') == hash_algo

        # Clear hash data after deletion
        cp._installed_certificate_hash_data = []

        # Step 7-8: Optional second GetInstalledCertificateIds (handled by handler automatically)

    start_task.cancel()
