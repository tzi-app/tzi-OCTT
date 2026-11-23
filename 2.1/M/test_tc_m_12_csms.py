"""
Test case name      Retrieve certificates from Charging Station - CSMSRootCertificate
Test case Id        TC_M_12_CSMS
Use case Id(s)      M03
Requirement(s)      M03.FR.01

Requirement Details:
    M03.FR.01: The Charging Station SHALL respond with a GetInstalledCertificateIdsResponse.
        Precondition: After receiving a GetInstalledCertificateIdsRequest
System under test   CSMS

Description         The CSMS is able to retrieve the certificates installed at the Charging Station using the
                    GetInstalledCertificateIdsRequest message. It supports all available hash algorithms,
                    including SHA256, SHA384, and SHA512.

Purpose             To verify if the CSMS is able to retrieve the hashData from all CSMSRootCertificates
                    stored at the Charging Station, using all available hash algorithms, including SHA256,
                    SHA384, and SHA512.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate. The Test System
   responds with data hashed with SHA256.
2. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate. The Test System
   responds with data hashed with SHA384.
3. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate. The Test System
   responds with data hashed with SHA512.

Tool validations
N/a

Post scenario validations:
    N/a
"""
