"""
Test case name      Retrieve certificates from Charging Station - No matching certificate found
Test case Id        TC_M_19_CSMS
Use case Id(s)      M03
Requirement(s)      M03.FR.01, M03.FR.02

Requirement Details:
    M03.FR.01: The Charging Station SHALL respond with a GetInstalledCertificateIdsResponse.
        Precondition: After receiving a GetInstalledCertificateIdsRequest
    M03.FR.02: The Charging Station SHALL indicate this by setting status in the
               GetInstalledCertificateIdsResponse to NotFound.
        Precondition: M03.FR.01 AND No certificate matching certificateType was found
System under test   CSMS

Description         The CSMS is able to retrieve the certificates installed at the Charging Station using the
                    GetInstalledCertificateIdsRequest message.

Purpose             To verify if the CSMS is able to handle a response from the Charging Station indicating it
                    was not able to find a certificate for the requested criteria.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a GetInstalledCertificateIdsRequest with certificateType
               ManufacturerRootCertificate.

1. The CSMS sends a GetInstalledCertificateIdsRequest
2. The Test System responds with a GetInstalledCertificateIdsResponse
    - With status is NotFound
    - certificateHashDataChain is omitted.

Tool validations
* Step 1:
    Message: GetInstalledCertificateIdsRequest
    - certificateType is ManufacturerRootCertificate

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

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
async def test_tc_m_19(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger the CSMS to send a GetInstalledCertificateIdsRequest with
    #                certificateType ManufacturerRootCertificate.
    # 1. The CSMS sends a GetInstalledCertificateIdsRequest
    # 2. The Test System responds with a GetInstalledCertificateIdsResponse
    #    - With status is NotFound
    #    - certificateHashDataChain is omitted.
    cp.set_response('GetInstalledCertificateIds', status='NotFound')
    request = await cp.wait_for_request(
        'GetInstalledCertificateIds',
        manual_action=send_call(BASIC_AUTH_CP, 'GetInstalledCertificateIds',
                                {'certificateType': ['ManufacturerRootCertificate']}))
    assert request.certificate_type == ['ManufacturerRootCertificate'], \
        f"Expected GetInstalledCertificateIdsRequest.certificateType ManufacturerRootCertificate, " \
        f"got {request.certificate_type}"

    start_task.cancel()
