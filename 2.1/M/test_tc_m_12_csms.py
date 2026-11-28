"""
Test case name      Retrieve certificates from Charging Station - CSMSRootCertificate
Test case Id        TC_M_12_CSMS
Use case Id(s)      M03
Requirement(s)      M03.FR.01

Requirement Details:
    M03.FR.01: The Charging Station SHALL respond with a GetInstalledCertificateIdsResponse.
        Precondition: After receiving a GetInstalledCertificateIdsRequest
System under test   CSMS

Description         The CSMS is able to retrieve the certificates installed at the Charging Station using the
                    GetInstalledCertificateIdsRequest message. It supports all available hash algorithms,
                    including SHA256, SHA384, and SHA512.

Purpose             To verify if the CSMS is able to retrieve the hashData from all CSMSRootCertificates
                    stored at the Charging Station, using all available hash algorithms, including SHA256,
                    SHA384, and SHA512.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate. The Test System
   responds with data hashed with SHA256.
2. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate. The Test System
   responds with data hashed with SHA384.
3. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate. The Test System
   responds with data hashed with SHA512.

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.get_installed_certificates import get_installed_certificates
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_m_12(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate.
    #    The Test System responds with data hashed with SHA256.
    await get_installed_certificates(cp, 'CSMSRootCertificate', hash_algorithm='SHA256')

    # 2. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate.
    #    The Test System responds with data hashed with SHA384.
    await get_installed_certificates(cp, 'CSMSRootCertificate', hash_algorithm='SHA384')

    # 3. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate.
    #    The Test System responds with data hashed with SHA512.
    await get_installed_certificates(cp, 'CSMSRootCertificate', hash_algorithm='SHA512')

    start_task.cancel()
