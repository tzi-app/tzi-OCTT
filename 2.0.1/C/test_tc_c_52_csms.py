"""
Test case name      Authorization using Contract Certificates 15118 - Online - Central contract certificate validation - Accepted
Test case Id        TC_C_52_CSMS
Use case Id(s)      C07
Requirement(s)      C07.FR.04, C07.FR.05

Requirement Details:
    C07.FR.04: If the CSMS receives an AuthorizeRequest, it SHALL respond with
    an AuthorizeResponse including an authorization status.
    C07.FR.05: The CSMS SHALL verify validity of the certificate and certificate
    chain via real-time or cached OCSP data.

System under test   CSMS

Real-world flow (ISO 15118 Plug & Charge - central validation):
    This is the CENTRAL validation path. Unlike C50/C51 where the CS validates
    the certificate chain locally and only sends hash data for OCSP, here the
    CS sends the full certificate PEM and delegates ALL validation to the CSMS.

    1. EV    - Presents its contract certificate to the CS via ISO 15118.
    2. CS    - Does NOT validate the chain locally. Instead, it forwards the
               raw PEM certificate to the CSMS in the AuthorizeRequest
               (certificate field). The iso15118CertificateHashData field is
               ABSENT — the CS expects the CSMS to figure everything out.
    3. CSMS  - Must perform the full validation pipeline itself:
               a) Parse the PEM, extract X.509 certificate(s)
               b) Check temporal validity (notBefore / notAfter)
               c) Verify issuer/subject chain integrity + cryptographic signatures
               d) Extract the OCSP responder URL from the leaf certificate's
                  Authority Information Access (AIA) X.509 extension
               e) Compute issuerNameHash (SHA-256 of issuer DN DER),
                  issuerKeyHash (SHA-256 of issuer public key), and serialNumber
               f) Build an RFC 6960 OCSP request from those computed values
               g) POST it to the responder URL from step (d)
               h) Parse the OCSP response and check certStatus
               i) Respond: certificateStatus=Accepted if cert is valid and not
                  revoked; CertificateRevoked otherwise
    4. OCSP  - The CA/MO OCSP responder answers with the certificate's
               revocation status (good / revoked).

    Key difference from C50/C51:
    - C50/C51: CS provides iso15118CertificateHashData (including responderURL).
               CSMS just builds an OCSP request from the provided data.
    - C52:     CS provides only the certificate PEM. CSMS must extract the
               responder URL from the cert's AIA extension AND compute all hash
               values itself. This tests a much deeper code path.

What this test sets up:
    Since there is no real EV, CA, or OCSP infrastructure, the Test System's
    certificate chain is configured in certs/ (contract_pki.py, made by
    generate_contract_certs.sh): V2G root CA -> sub-CA -> contract certificate.
    - All keys are EC (P-256). The contract certificate's CN is the configured
      eMAID. The contract certificate and the sub-CA have an AIA extension with
      the OCSP responder URL http://localhost:19082/ocsp.
    - The test spins up the OCSP service of the Test System, mock_ocsp_responder.py,
      on the port of that URL. It answers about the certificate it is asked about
      ("good"), signed by the CA that issued it.

Prerequisite(s)
    - The configured eMAID is known by the CSMS as valid.
    - The contract certificate is signed (through the sub-CA) by the root CA that
      the CSMS is configured with, certs/v2g_root_ca.pem (tzi-csms:
      CONTRACT_CERTIFICATE_TRUSTED_CA_PEM_PATH).

Test Scenario
    1. Test loads the configured contract certificate chain; the contract
       certificate and its sub-CA name OCSP responder URL http://localhost:19082/ocsp
    2. Test starts a mock OCSP responder on port 19082 returning "good"
    3. CS (OCTT) sends AuthorizeRequest with eMAID + the contract certificate
       chain in PEM (iso15118CertificateHashData is ABSENT — CSMS must derive it)
    4. CSMS parses the cert, extracts the OCSP responder URL from the AIA
       extension, computes issuer hashes and serial number, builds an
       RFC 6960 OCSP request, and POSTs it to the mock responder
    5. Mock OCSP responder returns certStatus = good
    6. CSMS responds: idTokenInfo.status=Accepted, certificateStatus=Accepted
    7. CS sends TransactionEventRequest (triggerReason=Authorized)
    8. CSMS responds: idTokenInfo.status=Accepted
    9. Energy transfer starts

Validations
    * CSMS sent at least one OCSP request (verified by mock responder counter)
    * The OCSP requests are about certificates of the chain, among them the
      contract certificate (the Test System checks that the received request is
      valid; key type ECDSA; the chain contains a sub-CA)
    * AuthorizeResponse: idTokenInfo.status=Accepted, certificateStatus=Accepted
    * TransactionEventResponse: idTokenInfo.status=Accepted

Configuration
    EMAID_ID_TOKEN / EMAID_ID_TOKEN_TYPE:   eMAID token known as valid at the CSMS
"""

import asyncio
import pytest
import os
from urllib.parse import urlparse

from ocpp.v201.enums import (
    AuthorizationStatusEnumType as AuthorizationStatusType,
    TriggerReasonEnumType as TriggerReasonType,
    TransactionEventEnumType as TransactionEventType,
    AuthorizeCertificateStatusEnumType,
)
from ocpp.v201.call import TransactionEvent
from ocpp.v201.datatypes import IdTokenType
from tzi_charge_point import TziChargePoint
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from reusable_states.parking_bay_occupied import parking_bay_occupied
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, validate_schema
from mock_ocsp_responder import MockOCSPResponder
from contract_pki import contract_chain_pem, contract_chain_with_issuers, contract_ocsp_url

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

# The Test System's OCSP service listens where the configured certificates point (19082).
OCSP_PORT = urlparse(contract_ocsp_url()).port


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_52(connection):
    token_id = os.environ['EMAID_ID_TOKEN']
    token_type = os.environ['EMAID_ID_TOKEN_TYPE']
    evse_id = 1
    connector_id = 1

    # 1. The configured contract certificate chain (contract certificate + sub-CA, PEM); both
    #    name the mock OCSP responder in their AIA extension
    contract_certificate = contract_chain_pem()
    contract, sub_ca = contract_chain_with_issuers()[0]

    # 2. Start mock OCSP responder that returns "good"
    ocsp_responder = MockOCSPResponder(port=OCSP_PORT, cert_status="good")
    ocsp_responder.start()

    try:
        assert connection.open
        cp = TziChargePoint(BASIC_AUTH_CP, connection)

        start_task = asyncio.create_task(cp.start())
        await parking_bay_occupied(cp, evse_id=evse_id)
        await ev_connected_pre_session(cp, evse_id=evse_id, connector_id=connector_id)

        # 3. AuthorizeRequest with eMAID and certificate (NO iso15118CertificateHashData)
        #    CSMS must extract OCSP data from the certificate itself
        auth_response = await cp.send_authorization_request_with_iso15118(
            id_token=token_id,
            token_type=token_type,
            certificate=contract_certificate,
            iso15118_certificate_hash_data=None,
        )

        # 4. Verify the CSMS actually queried the mock OCSP responder
        assert ocsp_responder.requests_received > 0, "CSMS did not send an OCSP request to the mock responder"
        # The Test System checks that the requests it received are about certificates of the chain,
        # among them the contract certificate
        for request in ocsp_responder.requests:
            assert any(request.is_about(certificate, issuer) for certificate, issuer in contract_chain_with_issuers()), \
                f"OCSP request about a certificate that is not in the chain (serial {request.serial_number:X})"
        assert any(request.is_about(contract, sub_ca) for request in ocsp_responder.requests), \
            "CSMS did not ask about the contract certificate"

        # 6. CSMS responds: Accepted + certificateStatus Accepted
        assert auth_response is not None
        assert validate_schema(data=auth_response, schema_file_name='../schema/AuthorizeResponse.json')
        assert auth_response.id_token_info['status'] == AuthorizationStatusType.accepted
        assert auth_response.certificate_status == AuthorizeCertificateStatusEnumType.accepted

        transaction_id = generate_transaction_id()

        # 7. TransactionEventRequest: Authorized
        event = TransactionEvent(
            event_type=TransactionEventType.started,
            timestamp=now_iso(),
            trigger_reason=TriggerReasonType.authorized,
            seq_no=cp.next_seq_no(),
            transaction_info={
                "transaction_id": transaction_id,
                "charging_state": "EVConnected",
            },
            id_token=IdTokenType(id_token=token_id, type=token_type),
            evse={
                "id": evse_id,
                "connector_id": connector_id
            }
        )
        tx_response = await cp.send_transaction_event_request(event)

        # 8. CSMS responds: Accepted
        assert tx_response is not None
        assert validate_schema(data=tx_response, schema_file_name='../schema/TransactionEventResponse.json')
        assert tx_response.id_token_info is not None
        assert tx_response.id_token_info.status == AuthorizationStatusType.accepted

        # 9. Execute Reusable State EnergyTransferStarted
        await energy_transfer_started(cp, evse_id=evse_id, connector_id=connector_id, transaction_id=transaction_id)

        start_task.cancel()
    finally:
        ocsp_responder.stop()
