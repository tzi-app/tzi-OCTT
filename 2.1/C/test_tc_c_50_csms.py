"""
Test case name      Authorization using Contract Certificates 15118 - Online - Local contract certificate
                    validation - Accepted
Test case Id        TC_C_50_CSMS
Use case Id(s)      C07
Requirement(s)      C07.FR.04

Requirement Details:
    C07.FR.04: It SHALL respond with an AuthorizeResponse and SHALL include an authorization status value
               indicating acceptance or a reason for rejection.
        Precondition: If the CSMS receives an AuthorizeRequest.
System under test   CSMS

Description         The Charging Station is able to authorize with contract certificates when it supports ISO
                    15118.

Purpose             To verify if the CSMS is able to validate the certificate hash data and the provided
                    eMAID.

Prerequisite(s)     - The configured eMAID is known by the CSMS as valid.
                    - The configured contract certificate is valid.
                    - The CN of the configured contract certificate equals the configured eMAID.
                    - iso15118CertificateHashData has a responder URL that points to an OCSP service for Test
                      System.
                    - CSMS does not have a cached OCSP response for the contract certificate.

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession

Test Scenario
1. The Test System sends an AuthorizeRequest with:
    - idToken.idToken <Configured eMAID>
    - idToken.type eMAID
    - iso15118CertificateHashData contains <hashes from configured (V2G) certificate chain
2. The CSMS sends an OCSP request to responder URL of iso15118CertificateHashData to check validity
3. The Test System OCSP service reponds that certificate is valid.
4. The CSMS responds with a AuthorizeResponse
5. The Test System sends a TransactionEventRequest with:
    - triggerReason Authorized
6. The CSMS responds with a TransactionEventResponse
5. Execute Reusable State EnergyTransferStarted

Tool validations
* Step 2:
    CSMS sends an OCSP request for iso15118CertificateHashData
* Step 3:
    Test System checks that received request for iso15118CertificateHashData is valid
* Step 4:
    Message: AuthorizeResponse
    - idTokenInfo.status Accepted
    - certificateStatus Accepted
* Step 4:
    Message: TransactionEventResponse
    - idTokenInfo.status Accepted

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.10. Page 103 - (2026-09) - C07 Figure 26 is not binding [1343] - 2.10.1. Updated sequence diagrams for
        Authorization using Contract Certificates
        (Part 2 errata - applies to this test via use case C07)
        Use case C07 shows a sequence diagram for plug-and-charge with ISO 15118-2. This diagram is
        informational and not binding.

        The remark of the use case has been updated to mention this. The sequence diagram has been updated
        with a recommended flow.

        | No. | Type | Description |
        | 1 | Name | Authorization using Contract Certificates |
        | 2 | ID | C07 |
        | | … | … |
        | 8 | Remark(s) | In edition 1 of 15118, the message timeout of the PaymentDetailsReq/Res message is 5
          seconds. In case certificate verification cannot be completed in that time it is possible to
          complete this during the AuthorizationReq/Res, which can be extended up to 60 seconds. /  / When the
          Charging Station is offline, it is recommended to omit the payment option for ISO 15118 contract
          certificates from the ServiceDiscoveryRes and revert to External Identification Means (use case
          C08), because certificate status cannot be checked. /  / Figures 26 and 27 show a sequence diagram
          of a PnC authorization. These figures are informational and not binding. |

        `mermaid
        sequenceDiagram
        participant EV
        participant CS as Charging Station
        participant CSMS
        participant CA as (Sub)CA
        EV->>CS: ServiceDiscoveryReq()
        CS-->>EV: ServiceDiscoveryRes(PaymentServiceList: Contract, ExternalPayment)
        EV->>CS: PaymentServiceSelectionReq(paymentOption: Contract)
        CS-->>EV: PaymentServiceSelectionRes()
        alt Cached certificate checking
        EV->>CS: PaymentDetailsReq(ContractCertificateChain, EMAID)
        CS->>CS: validate certificate chain
        CS-->>EV: PaymentDetailsRes(GenChallenge)
        EV->>CS: AuthorizationReq(GenChallenge)
        CS->>CS: check signature of GenChallenge
        CS->>CSMS: AuthorizeRequest(idToken.EMAID, iso15118CertificateHashData[0..4])
        CSMS->>CSMS: check certificate against cached OCSP response
        CSMS->>CSMS: check idToken validity
        CSMS-->>CS: AuthorizeResponse(idTokenInfo, certificateStatus)
        CS-->>EV: AuthorizationRes(EVSEProcessing, ResponseCode)
        else Real-time certificate checking
        EV->>CS: PaymentDetailsReq(ContractCertificateChain, EMAID)
        CS->>CS: validate certificate chain
        CS-->>EV: PaymentDetailsRes(GenChallenge)
        EV->>CS: AuthorizationReq(GenChallenge)
        CS->>CS: check signature of GenChallenge
        CS->>CSMS: AuthorizeRequest(idToken.EMAID, iso15118CertificateHashData[0..4])
        CS-->>EV: AuthorizationRes(EVSEProcessing = OnGoing)
        CSMS->>CA: OCSP request()
        Note left of CA: Some delay...
        EV->>CS: AuthorizationReq( ... )
        CA->>CSMS: OCSP response()
        CSMS->>CSMS: check certificate against OCSP response
        CSMS->>CSMS: check idToken validity
        CSMS-->>CS: AuthorizeResponse(idTokenInfo, certificateStatus)
        CS-->>EV: AuthorizationRes(EVSEProcessing = Finished, ResponseCode)
        end
        `

        Figure 26. Authorization using Contract Certificates with ISO 15118-2

        `mermaid
        sequenceDiagram
        participant EV
        participant CS as Charging Station
        participant CSMS
        participant CA as (Sub)CA
        EV->>CS: AuthorizationSetupReq()
        CS-->>EV: AuthorizationSetupRes(AuthorizationServices, GenChallenge, SupportedProviders)
        alt Cached certificate checking
        EV->>CS: AuthorizationReq(SelectedAuthorizationService, GenChallenge, ContractCertificateChain)
        CS->>CS: validate certificate chain
        CS->>CS: check signature of GenChallenge
        CS->>CSMS: AuthorizeRequest(idToken = <EMAID>, iso15118CertificateHashData[0..4])
        CSMS->>CSMS: check certificate validity from cache()
        CSMS->>CSMS: check validity of idToken
        CSMS-->>CS: AuthorizeResponse(idTokenInfo, certificateStatus)
        CS-->>EV: AuthorizationRes(EVSEProcessing, ResponseCode)
        else Real-time certificate checking
        EV->>CS: AuthorizationReq(SelectedAuthorizationService, GenChallenge, ContractCertificateChain)
        CS->>CS: validate certificate chain
        CS->>CS: check signature of GenChallenge
        CS->>CSMS: AuthorizeRequest(idToken = <EMAID>, iso15118CertificateHashData[0..4])
        CSMS->>CA: OCSP request(iso15118CertificateHashData)
        CS-->>EV: AuthorizationRes(EVSEProcessing = Ongoing)
        Note left of CA: Some delay involved
        EV->>CS: AuthorizationReq(SelectedAuthorizationService, GenChallenge, ContractCertificateChain)
        CA-->>CSMS: OSCP response()
        CSMS->>CSMS: check validity of idToken
        CSMS-->>CS: AuthorizeResponse(idTokenInfo, certificateStatus)
        CS-->>EV: AuthorizationRes(EVSEProcessing = Finished, ResponseCode)
        end
        `

        Figure 27. Authorization using Contract Certificates with ISO 15118-20
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import TziChargePoint21
from contract_pki import contract_chain_hash_data, contract_chain_with_issuers
from mock_ocsp_responder import MockOCSPResponder
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
# The configured eMAID: known by the CSMS as valid, and the CN of the configured contract
# certificate
EMAID_ID_TOKEN = {'id_token': os.environ['EMAID_ID_TOKEN'], 'type': 'eMAID'}

# The OCSP service of the Test System, which the responder URL of the hash data points to
OCSP_PORT = 19080


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_50(connection):
    ocsp_responder = MockOCSPResponder(port=OCSP_PORT, cert_status="good")
    ocsp_responder.start()
    try:
        assert connection.open
        cp = TziChargePoint21(BASIC_AUTH_CP, connection)
        start_task = asyncio.create_task(cp.start())
        await booted(cp)

        # Reusable State: State is EVConnectedPreSession
        transaction_id = await ev_connected_pre_session(cp)

        # 1. The Test System sends an AuthorizeRequest with:
        #    - idToken.idToken <Configured eMAID>
        #    - idToken.type eMAID
        #    - iso15118CertificateHashData contains <hashes from configured (V2G) certificate
        #      chain>: the contract certificate and its sub-CA
        # 2. The CSMS sends an OCSP request to responder URL of iso15118CertificateHashData to
        #    check validity
        # 3. The Test System OCSP service responds that certificate is valid.
        # 4. The CSMS responds with a AuthorizeResponse
        response = await cp.send_authorization_request_with_iso15118(
            id_token=EMAID_ID_TOKEN['id_token'],
            token_type=EMAID_ID_TOKEN['type'],
            iso15118_certificate_hash_data=contract_chain_hash_data(f"http://localhost:{OCSP_PORT}/ocsp"),
        )

        # Step 2: CSMS sends an OCSP request for iso15118CertificateHashData
        assert ocsp_responder.requests_received > 0, \
            "The CSMS did not send an OCSP request to the responder URL of the hash data"
        # Step 3: Test System checks that received request for iso15118CertificateHashData is
        # valid: it is about a certificate of the hash data
        for request in ocsp_responder.requests:
            assert any(request.is_about(certificate, issuer)
                       for certificate, issuer in contract_chain_with_issuers()), \
                f"OCSP request about a certificate that is not in the hash data " \
                f"(serial {request.serial_number:X})"

        # Step 4: idTokenInfo.status Accepted, certificateStatus Accepted
        validate_id_token_info('AuthorizeResponse', response.id_token_info, status='Accepted')
        assert response.certificate_status == 'Accepted', \
            f"Expected AuthorizeResponse.certificateStatus Accepted, got {response.certificate_status}"

        # 5. The Test System sends a TransactionEventRequest with triggerReason Authorized
        # 6. The CSMS responds with a TransactionEventResponse
        response = await cp.call(call.TransactionEvent(
            event_type='Updated',
            timestamp=utc_now_iso(),
            trigger_reason='Authorized',
            seq_no=cp.next_seq_no(),
            transaction_info={'transaction_id': transaction_id},
            id_token=EMAID_ID_TOKEN,
        ))
        validate_id_token_info('TransactionEventResponse', response.id_token_info, status='Accepted')
        cp.session.state = 'Authorized'
        cp.session.authorized = True
        cp.session.id_token = EMAID_ID_TOKEN

        # Execute Reusable State EnergyTransferStarted
        await energy_transfer_started(cp)

        start_task.cancel()
    finally:
        ocsp_responder.stop()
