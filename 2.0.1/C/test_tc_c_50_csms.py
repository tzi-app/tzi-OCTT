"""
Test case name      Authorization using Contract Certificates 15118 - Online - Local contract certificate validation - Accepted
Test case Id        TC_C_50_CSMS
Use case Id(s)      C07
Requirement(s)      C07.FR.04

Requirement Details:
    C07.FR.04: If the CSMS receives an AuthorizeRequest, it SHALL respond with
    an AuthorizeResponse and SHALL include an authorization status value
    indicating acceptance or a reason for rejection.

System under test   CSMS

Real-world flow (ISO 15118 Plug & Charge):
    1. EV    - The Electric Vehicle holds a contract certificate issued by a
               Mobility Operator (MO). During ISO 15118 session setup the EV
               presents this certificate to the Charging Station over the PLC
               (Power Line Communication) link.
    2. CS    - The Charging Station validates the certificate chain locally
               (ISO 15118 TLS handshake). It then sends an AuthorizeRequest to
               the CSMS containing:
                 - idToken (eMAID from the contract certificate)
                 - iso15118CertificateHashData (issuer hashes, serial number,
                   and the OCSP responder URL extracted from the certificate's
                   Authority Information Access extension)
               The CS does NOT send the certificate PEM itself — it already
               validated the chain. It only asks the CSMS to verify revocation
               status via OCSP.
    3. CSMS  - The CSMS builds an RFC 6960 OCSP request from the hash data and
               POSTs it to the responderURL. If the OCSP responder says "good",
               the CSMS responds with certificateStatus=Accepted. If "revoked"
               or unreachable, it responds CertificateRevoked.
    4. OCSP  - An external OCSP responder (operated by the CA / MO) answers
               whether the contract certificate has been revoked.

    In this test there is no real EV or real CA. The test spins up a mock OCSP
    responder (mock_ocsp_responder.py) on localhost that returns "good" for any
    query, and provides synthetic hash data pointing to it. This validates that
    the CSMS correctly queries the responder URL from the received hash data
    and accepts the authorization when the certificate is not revoked.

Prerequisite(s)
    - The configured eMAID is known by the CSMS as valid.

Test Scenario
    1. Test starts a mock OCSP responder on localhost:{OCSP_PORT} returning "good"
    2. CS (OCTT) sends AuthorizeRequest with eMAID + iso15118CertificateHashData
       (responderURL points to the mock OCSP responder)
    3. CSMS queries the mock OCSP responder at the responderURL
    4. Mock OCSP responder returns certStatus = good
    5. CSMS responds: idTokenInfo.status=Accepted, certificateStatus=Accepted
    6. CS sends TransactionEventRequest (triggerReason=Authorized)
    7. CSMS responds: idTokenInfo.status=Accepted
    8. Energy transfer starts

Validations
    * CSMS sent at least one OCSP request (verified by mock responder counter)
    * AuthorizeResponse: idTokenInfo.status=Accepted, certificateStatus=Accepted
    * TransactionEventResponse: idTokenInfo.status=Accepted

Configuration
    EMAID_ID_TOKEN / EMAID_ID_TOKEN_TYPE:   eMAID token known as valid at the CSMS
"""

import asyncio
import pytest
import os

from ocpp.v201.enums import (
    AuthorizationStatusEnumType as AuthorizationStatusType,
    TriggerReasonEnumType as TriggerReasonType,
    TransactionEventEnumType as TransactionEventType,
    AuthorizeCertificateStatusEnumType,
    HashAlgorithmEnumType,
)
from ocpp.v201.call import TransactionEvent
from ocpp.v201.datatypes import IdTokenType, OCSPRequestDataType
from tzi_charge_point import TziChargePoint
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from reusable_states.parking_bay_occupied import parking_bay_occupied
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, validate_schema
from mock_ocsp_responder import MockOCSPResponder

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

OCSP_PORT = 19080


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_50(connection):
    token_id = os.environ['EMAID_ID_TOKEN']
    token_type = os.environ['EMAID_ID_TOKEN_TYPE']
    evse_id = 1
    connector_id = 1

    # 1. Start mock OCSP responder that returns "good"
    ocsp_responder = MockOCSPResponder(port=OCSP_PORT, cert_status="good")
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
                issuer_name_hash="dGVzdC1pc3N1ZXItbmFtZS1oYXNo",
                issuer_key_hash="dGVzdC1pc3N1ZXIta2V5LWhhc2g=",
                serial_number="1A2B3C4D",
                responder_url=f"http://localhost:{OCSP_PORT}/ocsp",
            )
        ]

        # 2. AuthorizeRequest with eMAID idToken and iso15118CertificateHashData
        auth_response = await cp.send_authorization_request_with_iso15118(
            id_token=token_id,
            token_type=token_type,
            iso15118_certificate_hash_data=iso15118_cert_hash_data,
        )

        # 3. Verify the CSMS actually queried the mock OCSP responder
        assert ocsp_responder.requests_received > 0, "CSMS did not send an OCSP request to the mock responder"

        # 5. CSMS responds: Accepted + certificateStatus Accepted
        assert auth_response is not None
        assert validate_schema(data=auth_response, schema_file_name='../schema/AuthorizeResponse.json')
        assert auth_response.id_token_info['status'] == AuthorizationStatusType.accepted
        assert auth_response.certificate_status == AuthorizeCertificateStatusEnumType.accepted

        transaction_id = generate_transaction_id()

        # 6. TransactionEventRequest: Authorized
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

        # 7. CSMS responds: Accepted
        assert tx_response is not None
        assert validate_schema(data=tx_response, schema_file_name='../schema/TransactionEventResponse.json')
        assert tx_response.id_token_info is not None
        assert tx_response.id_token_info.status == AuthorizationStatusType.accepted

        # 8. Execute Reusable State EnergyTransferStarted
        await energy_transfer_started(cp, evse_id=evse_id, connector_id=connector_id, transaction_id=transaction_id)

        start_task.cancel()
    finally:
        ocsp_responder.stop()
