"""
Test case name      Authorization using Contract Certificates 15118 - Online - Local contract certificate
                    validation - Rejected
Test case Id        TC_C_51_CSMS
Use case Id(s)      C07
Requirement(s)      C07.FR.16

Requirement Details:
    C07.FR.16: CSMS SHALL return an AuthorizationResponse containing a certificateStatus = CertificateRevoked
               and an idTokenInfo.status = Invalid
        Precondition: C07.FR.04 AND the certificate chain (provided in certificate or
                      iso15118CertificateHashData) has been revoked
        Note: If certificate is revoked, then status of idToken is reported as invalid.
System under test   CSMS

Description         The Charging Station is able to authorize with contract certificates when it supports ISO
                    15118.

Purpose             To verify if the CSMS is able to validate the certificate hash data and the provided
                    eMAID.

Prerequisite(s)     - The configured eMAID is known by the CSMS as valid.
                    - The contract certificate is revoked.
                    - iso15118CertificateHashData has a responder URL that points to an OCSP service for Test
                      System.
                    - CSMS does not have a cached OCSP response for the contract certificate.

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession

Test Scenario
1. The Test System sends an AuthorizeRequest with:
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
    - iso15118CertificateHashData contains <hashes from configured (V2G) certificate chain
2. The CSMS sends an OCSP request to responder URL of iso15118CertificateHashData to check validity
3. The Test System OCSP service reponds that certificate is valid.
4. The CSMS responds with a AuthorizeResponse

Tool validations
* Step 2:
    CSMS sends an OCSP request for iso15118CertificateHashData
* Step 3:
    Test System checks that received request for iso15118CertificateHashData is valid
* Step 4:
    Message: AuthorizeResponse
    - idTokenInfo.status Invalid
    - certificateStatus CertificateRevoked

Post scenario validations:
    EV is not authorized and shall not charge:
    Charging Station does not send TransactionEventRequest with:
    - triggerReason = Authorized or chargingState = Charging

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

    6.3.8. Page 1026 - (2026-06) - TC_C_51_CSMS - Corrected OCSP response and removed post scenario
        validations
        The OCSP response was previously incorrectly marked as valid, this has now been corrected to indicate
        a revoked status.

        Post-scenario validations have been removed, as they are not applicable to the CSMS.

        | Test case name | Authorization using Contract Certificates 15118 - Online - Local contract
          certificate validation - Rejected |
        | Test case Id | TC_C_51_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | 1. The Test System sends an AuthorizeRequest / With idToken.idToken <Configured
          valid_idtoken_idtoken> / idToken.type <Configured valid_idtoken_type> / iso15118CertificateHashData
          contains <hashes from configured (V2G) certificate chain | 2. The CSMS sends an OCSP request to
          responder URL of iso15118CertificateHashData to check validity |
        | 3. The Test System OCSP service responds that certificate is [removed: valid] revoked. | 4. The CSMS
          responds with a AuthorizeResponse |

        | Tool validations |
        | … |
        | Post scenario validations: / [removed: EV is not authorized and shall not charge:] / [removed:
          Charging Station does not send TransactionEventRequest with:] / [removed: - triggerReason =
          Authorized or chargingState = Charging] / N/a |
"""
