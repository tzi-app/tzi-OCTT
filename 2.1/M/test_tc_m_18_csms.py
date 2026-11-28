"""
Test case name      Retrieve certificates from Charging Station - All certificateTypes
Test case Id        TC_M_18_CSMS
Use case Id(s)      M03
Requirement(s)      M03.FR.01

Requirement Details:
    M03.FR.01: The Charging Station SHALL respond with a GetInstalledCertificateIdsResponse.
        Precondition: After receiving a GetInstalledCertificateIdsRequest
System under test   CSMS

Description         The CSMS is able to retrieve the certificates installed at the Charging Station using the
                    GetInstalledCertificateIdsRequest message.

Purpose             To verify if the CSMS is able to retrieve the hashData from all Root CA and
                    V2GCertificateChain certificates stored at the Charging Station.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a GetInstalledCertificateIdsRequest without certificateType.

1. The CSMS sends a GetInstalledCertificateIdsRequest
2. The Test System responds with a GetInstalledCertificateIdsResponse
    - With status is Accepted
    - certificateHashDataChain contains <The hashData of all certificates stored at the Test System
      truststore>

Tool validations
* Step 1:
    Message: GetInstalledCertificateIdsRequest
    - certificateType is omitted

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from certificates import trust_store
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
async def test_tc_m_18(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger the CSMS to send a GetInstalledCertificateIdsRequest without
    #                certificateType.
    # 1. The CSMS sends a GetInstalledCertificateIdsRequest
    # 2. The Test System responds with a GetInstalledCertificateIdsResponse
    #    - With status is Accepted
    #    - certificateHashDataChain contains <The hashData of all certificates stored at the Test
    #      System truststore>
    cp.set_response('GetInstalledCertificateIds', status='Accepted',
                    certificate_hash_data_chain=trust_store())
    request = await cp.wait_for_request(
        'GetInstalledCertificateIds',
        manual_action=send_call(BASIC_AUTH_CP, 'GetInstalledCertificateIds', {}))
    assert request.certificate_type is None, \
        f"GetInstalledCertificateIdsRequest.certificateType must be omitted, got {request.certificate_type}"

    start_task.cancel()
