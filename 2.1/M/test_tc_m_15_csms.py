"""
Test case name      Retrieve certificates from Charging Station - V2GCertificateChain
Test case Id        TC_M_15_CSMS
Use case Id(s)      M03
Requirement(s)      M03.FR.01, M03.FR.05

Requirement Details:
    M03.FR.01: The Charging Station SHALL respond with a GetInstalledCertificateIdsResponse.
        Precondition: After receiving a GetInstalledCertificateIdsRequest
    M03.FR.05: The Charging Station SHALL include the hash data for each installed certificate belonging to a
               V2G certificate chain. Sub CA certificates SHALL be placed as a childCertificate under the V2G
               Charging Station certificate.
        Precondition: When the Charging Station receives a GetInstalledCertificateIdsRequest with
                      certificateType V2GCertificateChain
System under test   CSMS

Description         The CSMS is able to retrieve the certificates installed at the Charging Station using the
                    GetInstalledCertificateIdsRequest message.

Purpose             To verify if the CSMS is able to retrieve the hashData from all certificates that are part
                    of a V2GCertificateChain stored at the Charging Station.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State GetInstalledCertificates for certificateType V2GCertificateChain

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
async def test_tc_m_15(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State GetInstalledCertificates for certificateType V2GCertificateChain
    await get_installed_certificates(cp, 'V2GCertificateChain')

    start_task.cancel()
