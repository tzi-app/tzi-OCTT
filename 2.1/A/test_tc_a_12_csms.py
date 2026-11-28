"""
Test case name      Update Charging Station Certificate by request of CSMS - Success - V2G Certificate
Test case Id        TC_A_12_CSMS
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

Prerequisite(s)     The CSMS supports ISO 15118.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse
    - status Accepted
3 The Test System sends a SignCertificateRequest
    - csr Generated CSR based on:
        - <Configured Country>
        - <Configured Organization>
        - <Configured OrganizationalUnit>
    - certificateType V2GCertificate
4. The CSMS responds with a SignCertificateResponse
5. The CSMS sends a CertificateSignedRequest
6. The Test System responds with a CertificateSignedResponse
    - status Accepted

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage SignV2GCertificate
* Step 4:
    Message: SignCertificateResponse
    - status Accepted
* Step 5:
    Message: CertificateSignedRequest
    - certificateChain <Certificate generated from the received CSR from step 3 and signed by the V2G Root or
      SubCA certificate from the configured V2G certificate chain>

    NOTE: The Test System will validate the certificate, but if the following validation fail, the testcase
          will NOT FAIL, because generating the certificate is probably not be done by the CSMS.

    - The key must be at least 224 bits long.
    - The received certificate must be transmitted in the X.509 format encoded in Privacy-Enhanced Mail (PEM)
      format.

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.7. Page 37 - (2026-02) - A02.FR.02 - Requirement reference correction
        (Part 2 errata - applies to this test via use case A02)
        | | ID | Precondition | Requirement definition | Note |
        | Old | A02.FR.02 | | The Charging Station SHALL generate a new public / private key pair using one of
          the key generation functions described in Section 4.2.1.3 of [16]. | |
        | New | A02.FR.02 | | The Charging Station SHALL generate a new public / private key pair using one of
          the key generation functions described in Section 8.1 of [27] . | |
"""

import asyncio
import os

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
async def test_tc_a_12():
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
                                      {'requestedMessage': 'SignV2GCertificate'}))
        assert trigger_message.requested_message == 'SignV2GCertificate', \
            f"Expected requestedMessage SignV2GCertificate, got: {trigger_message.requested_message}"

        # 3. The Test System sends a SignCertificateRequest
        #    - csr Generated CSR based on the configured Country, Organization and
        #      OrganizationalUnit
        #    - certificateType V2GCertificate
        # 4. The CSMS responds with a SignCertificateResponse
        csr, private_key = station_csr(cp_id)
        sign_response = await cp.call(call.SignCertificate(
            csr=csr,
            certificate_type='V2GCertificate',
        ))
        assert sign_response.status == 'Accepted', \
            f"Expected SignCertificateResponse.status Accepted, got: {sign_response.status}"

        # 5. The CSMS sends a CertificateSignedRequest
        # 6. The Test System responds with a CertificateSignedResponse - status Accepted
        certificate_signed = await cp.wait_for_request('CertificateSigned')

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
