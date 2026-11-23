"""
Test case name      Certificate Installation EV - ISO 15118-20 - Success
Test case Id        TC_M_100_CSMS
Use case Id(s)      M01
Requirement(s)      M01.FR.02, M01.FR.05

Requirement Details:
    M01.FR.02 (2.1): Charging Station SHALL NOT include the field maximumContractCertificateChains in the
                     Get15118EVCertificateRequest message.
        Precondition: When EV uses ISO 15118-2
    M01.FR.05 (2.1): Charging station SHALL update the value of RemainingContractCertificateChains in the ISO
                     15118-20 CertificateInstallationRes message to EV to the value of remainingContracts of
                     the OCPP Get15118EVCertificateResponse message.
        Precondition: When EV uses ISO 15118-20 AND Upon receiving a Get15118EVCertificateResponse from CSMS
System under test   CSMS

Description         The EV initiates installing a new certificate. The Charging Station forwards the request
                    for a new certificate to the CSMS.

Purpose             To verify if the CSMS is able to return the Raw CertificateInstallationRes response for
                    the EV to the Charging Station.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Note(s): 3 ContractCertificateChains will be communicated to the CSMS.

1. The Test System sends a Get15118EVCertificateRequest
    With action Install
    - maximumContractCertificateChains 10
    - prioritizedEMAIDs <Configured list EMA IDs>
2. The CSMS responds with a Get15118EVCertificateResponse
3. The Test System sends a Get15118EVCertificateRequest
    With action Install
    - maximumContractCertificateChains 10
    - prioritizedEMAIDs <Configured list EMA IDs>
4. The CSMS responds with a Get15118EVCertificateResponse
5. The Test System sends a Get15118EVCertificateRequest
    With action Install
    - maximumContractCertificateChains 10
    - prioritizedEMAIDs <Configured list EMA IDs>
6. The CSMS responds with a Get15118EVCertificateResponse

Tool validations
* Step 2:
    Message: Get15118EVCertificateResponse
    - status must be Accepted
    - exiResponse <Raw CertificateInstallationRes response for the EV, Base64 encoded.>
    - remainingContracts must be 2
* Step 4:
    Message: Get15118EVCertificateResponse
    - status must be Accepted
    - exiResponse <Raw CertificateInstallationRes response for the EV, Base64 encoded.>
    - remainingContracts must be 1
* Step 6:
    Message: Get15118EVCertificateResponse
    - status must be Accepted
    - exiResponse <Raw CertificateInstallationRes response for the EV, Base64 encoded.>
    - remainingContracts must be 0

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
