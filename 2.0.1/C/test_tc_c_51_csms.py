"""
Test case name      Authorization using Contract Certificates 15118 - Online - Local contract certificate validation - Rejected
Test case Id        TC_C_51_CSMS
Use case Id(s)      C07
Requirement(s)      C07.FR.16

Requirement Details:
    C07.FR.16: When the certificate chain has been revoked, the CSMS SHALL
    return certificateStatus=CertificateRevoked and idTokenInfo.status=Invalid.

System under test   CSMS

Real-world flow (ISO 15118 Plug & Charge - revoked certificate):
    This is the same flow as C50, but the contract certificate has been revoked
    by the Mobility Operator (e.g. the driver's contract was terminated).

    1. EV    - Presents its (now revoked) contract certificate to the CS via
               ISO 15118. The EV does not know the certificate has been revoked.
    2. CS    - Validates the chain locally (it still passes — revocation is not
               a chain property). Sends AuthorizeRequest with the eMAID and
               iso15118CertificateHashData to the CSMS.
    3. CSMS  - Builds an OCSP request from the hash data and queries the
               responderURL. The OCSP responder reports "revoked".
               CSMS responds: certificateStatus=CertificateRevoked,
               idTokenInfo.status=Invalid. The driver cannot charge.
    4. OCSP  - The CA/MO OCSP responder reports the certificate as revoked.

    In this test the test sends the hash data of the configured certificate
    chain of the Test System (contract_pki.py: V2G root CA -> sub-CA -> contract
    certificate). The mock OCSP responder (mock_ocsp_responder.py), the OCSP
    service of the Test System, answers that the contract certificate is revoked
    (its sub-CA stays good). Its answers are signed by the CA that issued the
    certificate, like a real responder's.

Prerequisite(s)
    - The configured eMAID is known by the CSMS as valid (token itself is OK,
      but the certificate is revoked so authorization must be rejected).
    - The contract certificate is revoked.
    - The CSMS is configured with the root CA of the chain, certs/v2g_root_ca.pem
      (tzi-csms: CONTRACT_CERTIFICATE_TRUSTED_CA_PEM_PATH).

Test Scenario
    1. Test starts a mock OCSP responder on localhost:{OCSP_PORT} that answers the
       contract certificate is revoked
    2. CS (OCTT) sends AuthorizeRequest with eMAID + iso15118CertificateHashData
       containing the hashes from the configured certificate chain (responderURL
       points to the mock OCSP responder)
    3. CSMS queries the mock OCSP responder at the responderURL
    4. Mock OCSP responder returns certStatus = revoked
    5. CSMS responds: idTokenInfo.status=Invalid, certificateStatus=CertificateRevoked

Validations
    * CSMS sent at least one OCSP request (verified by mock responder counter)
    * The OCSP requests are about certificates of the hash data (the Test System
      checks that the received request is valid)
    * AuthorizeResponse: idTokenInfo.status=Invalid, certificateStatus=CertificateRevoked

Configuration
    EMAID_ID_TOKEN / EMAID_ID_TOKEN_TYPE:   eMAID token known as valid at the CSMS
"""

import asyncio
import pytest
import os

from ocpp.v201.enums import (
    AuthorizationStatusEnumType as AuthorizationStatusType,
    AuthorizeCertificateStatusEnumType,
)
import contract_pki
from contract_pki import contract_chain_hash_data, contract_chain_with_issuers
from tzi_charge_point import TziChargePoint
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from reusable_states.parking_bay_occupied import parking_bay_occupied
from utils import get_basic_auth_headers, validate_schema
from mock_ocsp_responder import MockOCSPResponder

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

OCSP_PORT = 19081


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_51(connection):
    token_id = os.environ['EMAID_ID_TOKEN']
    token_type = os.environ['EMAID_ID_TOKEN_TYPE']
    evse_id = 1
    connector_id = 1

    # 1. Start mock OCSP responder that answers the contract certificate is revoked
    contract_certificate = contract_pki.load_certificate(contract_pki.CONTRACT)
    ocsp_responder = MockOCSPResponder(port=OCSP_PORT, revoked_serials={contract_certificate.serial_number})
    ocsp_responder.start()

    try:
        assert connection.open
        cp = TziChargePoint(BASIC_AUTH_CP, connection)

        start_task = asyncio.create_task(cp.start())
        await parking_bay_occupied(cp, evse_id=evse_id)
        await ev_connected_pre_session(cp, evse_id=evse_id, connector_id=connector_id)

        # Hash data of the configured contract certificate chain (the contract certificate and its
        # sub-CA), with the responder URL of the Test System's OCSP service: our mock
        iso15118_cert_hash_data = contract_chain_hash_data(f"http://localhost:{OCSP_PORT}/ocsp")

        # 2. AuthorizeRequest with eMAID idToken and iso15118CertificateHashData (revoked cert)
        auth_response = await cp.send_authorization_request_with_iso15118(
            id_token=token_id,
            token_type=token_type,
            iso15118_certificate_hash_data=iso15118_cert_hash_data,
        )

        # 3. Verify the CSMS actually queried the mock OCSP responder
        assert ocsp_responder.requests_received > 0, "CSMS did not send an OCSP request to the mock responder"
        # The Test System checks that the requests it received are about certificates of the hash data
        for request in ocsp_responder.requests:
            assert any(request.is_about(certificate, issuer) for certificate, issuer in contract_chain_with_issuers()), \
                f"OCSP request about a certificate that is not in the hash data (serial {request.serial_number:X})"

        # 5. CSMS responds: authorization rejected because the certificate is revoked
        assert auth_response is not None
        assert validate_schema(data=auth_response, schema_file_name='../schema/AuthorizeResponse.json')
        assert auth_response.id_token_info['status'] == AuthorizationStatusType.invalid
        assert auth_response.certificate_status == AuthorizeCertificateStatusEnumType.certificate_revoked

        start_task.cancel()
    finally:
        ocsp_responder.stop()
