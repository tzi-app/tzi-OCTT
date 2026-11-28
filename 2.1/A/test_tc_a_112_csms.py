"""
ADDED by OCPP 2.1 Edition 2 errata 2026-09 (5.3, 6.1.1) - transcribed from the errata document.

Test case name      Update Charging Station Certificate by request of CSMS - Success - V2G Certificate -20
Test case Id        TC_A_112_CSMS
Use case Id(s)      A02 & F06
Requirement(s)      A02.FR.11, F06.FR.01

Requirement Details:
    A02.FR.11: The CSMS SHALL set status to Accepted in the SignCertificateResponse.
        Precondition: Upon receipt of a SignCertificateRequest AND It is able to process the request
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to update its charging station
                    certificate using the TriggerMessageRequest message.

Purpose             To verify if the CSMS is able to request the Charging Station to update its V2G
                    Certificate.

Prerequisite(s)     The CSMS supports ISO 15118-20.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse
    - status Accepted
3. The Test System sends a SignCertificateRequest
    - csr Generated CSR based on:
        - <Configured Country>
        - <Configured Organization>
        - <Configured OrganizationalUnit>
    - certificateType V2G20Certificate
    - requestId <Generated requestId>
4. The CSMS responds with a SignCertificateResponse
5. The CSMS sends a CertificateSignedRequest
6. The Test System responds with a CertificateSignedResponse
    - status Accepted

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage SignV2G20Certificate
* Step 4:
    Message: SignCertificateResponse
    - status Accepted
* Step 5:
    Message: CertificateSignedRequest
    - certificateType V2G20Certificate
    - certificateChain <Certificate generated from the received CSR from step 3 and signed by the V2G Root or
      SubCA certificate from the configured V2G certificate chain>

    NOTE: The Test System will validate the certificate, but if the following validation fail, the testcase
          will NOT FAIL, because generating the certificate is probably not be done by the CSMS.

    - The key must be at least 224 bits long.
    - The received certificate must be transmitted in the X.509 format encoded in Privacy-Enhanced Mail (PEM)
      format.

Post scenario validations:
    N/a
"""

import asyncio
import os
import random

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from security import (
    V2G_ROOT_CERT,
    V2G_SUB_CA_CERT,
    connect_with_profile,
    report_certificate_properties,
    station_csr,
    validate_signed_certificate,
)
from trigger import trigger_v21

SECURITY_PROFILE_3_CP = os.environ['CP21_SP3']


@pytest.mark.asyncio
async def test_tc_a_112():
    cp_id = SECURITY_PROFILE_3_CP

    ws = await connect_with_profile(cp_id, security_profile=3)
    try:
        cp = TziChargePoint21(cp_id, ws)
        start_task = asyncio.create_task(cp.start())

        # 1. The CSMS sends a TriggerMessageRequest
        # 2. The Test System responds with a TriggerMessageResponse - status Accepted
        trigger_message = await cp.wait_for_request(
            'TriggerMessage',
            manual_action=trigger_v21(cp_id, 'trigger-message',
                                      {'requestedMessage': 'SignV2G20Certificate'}))
        assert trigger_message.requested_message == 'SignV2G20Certificate', \
            f"Expected requestedMessage SignV2G20Certificate, got: {trigger_message.requested_message}"

        # 3. The Test System sends a SignCertificateRequest
        #    - csr Generated CSR based on the configured Country, Organization and
        #      OrganizationalUnit
        #    - certificateType V2G20Certificate
        #    - requestId <Generated requestId>
        # 4. The CSMS responds with a SignCertificateResponse
        csr, private_key = station_csr(cp_id)
        request_id = random.randint(1, 2 ** 31 - 1)
        sign_response = await cp.call(call.SignCertificate(
            csr=csr,
            certificate_type='V2G20Certificate',
            request_id=request_id,
        ))
        assert sign_response.status == 'Accepted', \
            f"Expected SignCertificateResponse.status Accepted, got: {sign_response.status}"

        # 5. The CSMS sends a CertificateSignedRequest
        # 6. The Test System responds with a CertificateSignedResponse - status Accepted
        certificate_signed = await cp.wait_for_request('CertificateSigned')
        assert certificate_signed.certificate_type == 'V2G20Certificate', \
            f"Expected certificateType V2G20Certificate, got: {certificate_signed.certificate_type}"
        # The station can only answer Accepted to the CertificateSignedRequest of its own
        # request: with an unknown requestId it answers Rejected (A02.FR.26). The CSMS has to
        # include the requestId of the SignCertificateRequest (A02.FR.25).
        assert certificate_signed.request_id == request_id, \
            f"Expected the requestId of the SignCertificateRequest ({request_id}), " \
            f"got: {certificate_signed.request_id}"

        # certificateChain: the certificate generated from the received CSR from step 3 and
        # signed by the V2G Root or SubCA certificate from the configured V2G certificate chain
        certificates = validate_signed_certificate(
            certificate_signed.certificate_chain, private_key, V2G_ROOT_CERT,
            sub_ca_certificate_paths=[V2G_SUB_CA_CERT])

        # The key length and the X.509 PEM format are validated as well, but they do NOT
        # fail the test case.
        report_certificate_properties(certificates)

        start_task.cancel()
    finally:
        await ws.close()
