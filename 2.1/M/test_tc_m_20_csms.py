"""
Test case name      Delete a certificate from a Charging Station - Success
Test case Id        TC_M_20_CSMS
Use case Id(s)      M04
Requirement(s)      M04.FR.01, M04.FR.07

Requirement Details:
    M04.FR.01: The Charging Station SHALL respond with a DeleteCertificateResponse.
        Precondition: After receiving a DeleteCertificateRequest
    M04.FR.07: The CSMS SHALL use the same hashAlgorithm as the Charging Station uses to report the
               certificateHashData for the certificate in the GetInstalledCertificateIdsResponse.
        Precondition: When deleting a certificate
        Note: This ensures CSMS uses a hashAlgorithm that is supported by the Charging Station.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to delete an installed certificate using
                    the DeleteCertificateRequest message, using all available hash algorithms, including
                    SHA256, SHA384, and SHA512.

Purpose             To verify if CSMS is able to request a Charging Station to delete an installed
                    certificate, using all available hash algorithms, including SHA256, SHA384, and SHA512.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. CertificateInstalled with certificateType CSMSRootCertificate.

Manual Action: Request the CSMS to send a DeleteCertificateRequest.

2. The CSMS sends a GetInstalledCertificateIdsRequest
3. The Test System responds with a GetInstalledCertificateIdsResponse
    - With status is Accepted
    - certificateHashDataChain contains an entry with following values:
    - certificateHashDataChain[0].certificateType is CSMSRootCertificate
    - certificateHashDataChain[0].certificateHashData.hashAlgorithm is SHA256
4. The CSMS sends a DeleteCertificateRequest
5. The Test System responds with a DeleteCertificateResponse
    - With status is Accepted

Note(s):
- Steps 1 - 5 will be repeated for each hash algorithm (SHA256, SHA384, SHA512).

Tool validations
* Step 2:
    Message: GetInstalledCertificateIdsRequest
    - certificateType contains CSMSRootCertificate OR is omitted.
* Step 4:
    Message: DeleteCertificateRequest
    - certificateHashData is <Returned certificateHashData at Step 3>.

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from certificates import certificate_hash_data_chain
from charge_point import TziChargePoint21
from ocpp_messages import to_ocpp
from reusable_states.booted import booted
from reusable_states.certificate_installed import certificate_installed
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_m_20(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Note(s): Steps 1 - 5 will be repeated for each hash algorithm (SHA256, SHA384, SHA512).
    for hash_algorithm in ('SHA256', 'SHA384', 'SHA512'):
        # 1. CertificateInstalled with certificateType CSMSRootCertificate.
        await certificate_installed(cp, 'CSMSRootCertificate')

        # Manual Action: Request the CSMS to send a DeleteCertificateRequest.
        # 2. The CSMS sends a GetInstalledCertificateIdsRequest
        # 3. The Test System responds with a GetInstalledCertificateIdsResponse
        #    - With status is Accepted
        #    - certificateHashDataChain[0].certificateType is CSMSRootCertificate
        #    - certificateHashDataChain[0].certificateHashData.hashAlgorithm is the hash
        #      algorithm of this round
        installed = certificate_hash_data_chain('CSMSRootCertificate', hash_algorithm)
        cp.set_response('GetInstalledCertificateIds', status='Accepted',
                        certificate_hash_data_chain=[installed])
        request = await cp.wait_for_request(
            'GetInstalledCertificateIds',
            manual_action=send_call(BASIC_AUTH_CP, 'GetInstalledCertificateIds',
                                    {'certificateType': ['CSMSRootCertificate']}))
        # certificateType contains CSMSRootCertificate OR is omitted.
        assert request.certificate_type is None or 'CSMSRootCertificate' in request.certificate_type, \
            f"Expected GetInstalledCertificateIdsRequest.certificateType with CSMSRootCertificate, " \
            f"or omitted, got {request.certificate_type}"

        # 4. The CSMS sends a DeleteCertificateRequest
        # 5. The Test System responds with a DeleteCertificateResponse
        #    - With status is Accepted
        hash_data = installed['certificate_hash_data']
        cp.set_response('DeleteCertificate', status='Accepted')
        request = await cp.wait_for_request(
            'DeleteCertificate',
            manual_action=send_call(BASIC_AUTH_CP, 'DeleteCertificate', to_ocpp(
                'DeleteCertificateRequest', {'certificate_hash_data': hash_data})))
        # certificateHashData is <Returned certificateHashData at Step 3>.
        assert dict(request.certificate_hash_data) == hash_data, \
            f"Expected DeleteCertificateRequest.certificateHashData {hash_data}, " \
            f"got {dict(request.certificate_hash_data)}"

    start_task.cancel()
