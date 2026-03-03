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

    In this test the mock OCSP responder (mock_ocsp_responder.py) is
    configured to return "revoked" for any query, simulating a revoked
    contract certificate.

Prerequisite(s)
    - The configured eMAID is known by the CSMS as valid (token itself is OK,
      but the certificate is revoked so authorization must be rejected).

Test Scenario
    1. Test starts a mock OCSP responder on localhost:{OCSP_PORT} returning "revoked"
    2. CS (OCTT) sends AuthorizeRequest with eMAID + iso15118CertificateHashData
       (responderURL points to the mock OCSP responder)
    3. CSMS queries the mock OCSP responder at the responderURL
    4. Mock OCSP responder returns certStatus = revoked
    5. CSMS responds: idTokenInfo.status=Invalid, certificateStatus=CertificateRevoked

Validations
    * CSMS sent at least one OCSP request (verified by mock responder counter)
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
    HashAlgorithmEnumType,
)
from ocpp.v201.datatypes import OCSPRequestDataType
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

    # 1. Start mock OCSP responder that returns "revoked"
    ocsp_responder = MockOCSPResponder(port=OCSP_PORT, cert_status="revoked")
    ocsp_responder.start()

    try:
        assert connection.open
        cp = TziChargePoint(BASIC_AUTH_CP, connection)

        start_task = asyncio.create_task(cp.start())
        await parking_bay_occupied(cp, evse_id=evse_id)
        await ev_connected_pre_session(cp, evse_id=evse_id, connector_id=connector_id)

        # Build hash data pointing to our mock responder
        iso15118_cert_hash_data = [
            OCSPRequestDataType(
                hash_algorithm=HashAlgorithmEnumType.sha256,
                issuer_name_hash="cmV2b2tlZC1pc3N1ZXItbmFtZS1oYXNo",
                issuer_key_hash="cmV2b2tlZC1pc3N1ZXIta2V5LWhhc2g=",
                serial_number="DEADBEEF",
                responder_url=f"http://localhost:{OCSP_PORT}/ocsp",
            )
        ]

        # 2. AuthorizeRequest with eMAID idToken and iso15118CertificateHashData (revoked cert)
        auth_response = await cp.send_authorization_request_with_iso15118(
            id_token=token_id,
            token_type=token_type,
            iso15118_certificate_hash_data=iso15118_cert_hash_data,
        )

        # 3. Verify the CSMS actually queried the mock OCSP responder
        assert ocsp_responder.requests_received > 0, "CSMS did not send an OCSP request to the mock responder"

        # 5. CSMS responds: authorization rejected because the certificate is revoked
        assert auth_response is not None
        assert validate_schema(data=auth_response, schema_file_name='../schema/AuthorizeResponse.json')
        assert auth_response.id_token_info['status'] == AuthorizationStatusType.invalid
        assert auth_response.certificate_status == AuthorizeCertificateStatusEnumType.certificate_revoked

        start_task.cancel()
    finally:
        ocsp_responder.stop()
