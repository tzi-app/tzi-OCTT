"""
Test case name      Retrieve certificates from Charging Station - All certificateTypes
Test case Id        TC_M_18_CSMS
Use case Id(s)      M03
Requirement(s)      M03.FR.01

Requirement Details:
    M03.FR.01: The Charging Station SHALL respond with a GetInstalledCertificateIdsResponse.
        Precondition: After receiving a GetInstalledCertificateIdsRequest
System under test   CSMS

Description         The CSMS is able to retrieve the certificates installed at the Charging Station using the
                    GetInstalledCertificateIdsRequest message.

Purpose             To verify if the CSMS is able to retrieve the hashData from all Root CA and
                    V2GCertificateChain certificates stored at the Charging Station.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a GetInstalledCertificateIdsRequest without certificateType.

1. The CSMS sends a GetInstalledCertificateIdsRequest
2. The Test System responds with a GetInstalledCertificateIdsResponse
    - With status is Accepted
    - certificateHashDataChain contains <The hashData of all certificates stored at the Test System
      truststore>

Tool validations
* Step 1:
    Message: GetInstalledCertificateIdsRequest
    - certificateType is omitted

Post scenario validations:
    N/a
"""
