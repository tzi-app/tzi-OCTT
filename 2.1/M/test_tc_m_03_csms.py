"""
Test case name      Install CA certificate - V2GRootCertificate
Test case Id        TC_M_03_CSMS
Use case Id(s)      M05
Requirement(s)      M05.FR.01

Requirement Details:
    M05.FR.01: The Charging Station SHALL attempt to install the certificate and respond with an
               InstallCertificateResponse.
        Precondition: After receiving an InstallCertificateRequest
System under test   CSMS

Description         The CSMS is able to request the Charging Station to install new Root CA certificates using
                    the InstallCertificateRequest message.

Purpose             To verify if the CSMS is able to request a Charging Station to install a new
                    V2GRootCertificate.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State CertificateInstalled for certificateType V2GRootCertificate

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
from reusable_states.certificate_installed import certificate_installed
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_m_03(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State CertificateInstalled for certificateType V2GRootCertificate
    await certificate_installed(cp, 'V2GRootCertificate')

    start_task.cancel()
