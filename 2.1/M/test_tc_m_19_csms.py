"""
Test case name      Retrieve certificates from Charging Station - No matching certificate found
Test case Id        TC_M_19_CSMS
Use case Id(s)      M03
Requirement(s)      M03.FR.01, M03.FR.02

Requirement Details:
    M03.FR.01: The Charging Station SHALL respond with a GetInstalledCertificateIdsResponse.
        Precondition: After receiving a GetInstalledCertificateIdsRequest
    M03.FR.02: The Charging Station SHALL indicate this by setting status in the
               GetInstalledCertificateIdsResponse to NotFound.
        Precondition: M03.FR.01 AND No certificate matching certificateType was found
System under test   CSMS

Description         The CSMS is able to retrieve the certificates installed at the Charging Station using the
                    GetInstalledCertificateIdsRequest message.

Purpose             To verify if the CSMS is able to handle a response from the Charging Station indicating it
                    was not able to find a certificate for the requested criteria.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a GetInstalledCertificateIdsRequest with certificateType
               ManufacturerRootCertificate.

1. The CSMS sends a GetInstalledCertificateIdsRequest
2. The Test System responds with a GetInstalledCertificateIdsResponse
    - With status is NotFound
    - certificateHashDataChain is omitted.

Tool validations
* Step 1:
    Message: GetInstalledCertificateIdsRequest
    - certificateType is ManufacturerRootCertificate

Post scenario validations:
    N/a
"""
