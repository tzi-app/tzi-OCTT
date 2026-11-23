"""
Test case name      Certificate Update EV - Success
Test case Id        TC_M_28_CSMS
Use case Id(s)      M02
Requirement(s)      M02.FR.01

Requirement Details:
    M02.FR.01 (2.1): Charging Station SHALL forward the request to the CSMS using the
                     Get15118EVCertificateRequest message with action = Update.
        Precondition: Upon receiving an ISO 15118 CertificateUpdateReq AND EV uses ISO 15118-2
        Note: The CSMS is responsible for forwarding it to the secondary actor which will process the
              CertificateUpdateRequest. This could be a contract certificate pool as outlined in application
              guide VDE-AR-E 2802-100-1.
System under test   CSMS

Description         The EV initiates updating the existing certificate. The Charging Station forwards the
                    update request to the CSMS.

Purpose             To verify if the CSMS is able to return the Raw CertificateInstallationRes response for
                    the EV to the Charging Station.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a Get15118EVCertificateRequest
    With action Update
2. The CSMS responds with a Get15118EVCertificateResponse

Tool validations
* Step 2:
    Message: Get15118EVCertificateResponse
    - status Accepted
    - exiResponse <Raw CertificateInstallationRes response for the EV, Base64 encoded.>

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.16. Page 1264/1265/1266 - (2026-09) - TC_M_100_CSMS / TC_M_26_CSMS / TC_M_28_CSMS - Included
        iso15118SchemaVersion information
        | Test case name | Certificate Installation EV - ISO 15118-20 - Success |
        | Test case Id | TC_M_100_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | Note(s): 3 ContractCertificateChains will be communicated to the CSMS. | |

        | Test case Id | TC_M_26_CSMS / TC_M_28_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | 1. The Test System sends a Get15118EVCertificateRequest / With action Update / iso15118SchemaVersion
          urn:iso:15118:2:2013:MsgDef | 2. The CSMS responds with a Get15118EVCertificateResponse |
"""
