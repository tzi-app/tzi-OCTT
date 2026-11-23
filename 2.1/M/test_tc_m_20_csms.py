"""
Test case name      Delete a certificate from a Charging Station - Success
Test case Id        TC_M_20_CSMS
Use case Id(s)      M04
Requirement(s)      M04.FR.01, M04.FR.07

Requirement Details:
    M04.FR.01: The Charging Station SHALL respond with a DeleteCertificateResponse.
        Precondition: After receiving a DeleteCertificateRequest
    M04.FR.07: The CSMS SHALL use the same hashAlgorithm as the Charging Station uses to report the
               certificateHashData for the certificate in the GetInstalledCertificateIdsResponse.
        Precondition: When deleting a certificate
        Note: This ensures CSMS uses a hashAlgorithm that is supported by the Charging Station.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to delete an installed certificate using
                    the DeleteCertificateRequest message, using all available hash algorithms, including
                    SHA256, SHA384, and SHA512.

Purpose             To verify if CSMS is able to request a Charging Station to delete an installed
                    certificate, using all available hash algorithms, including SHA256, SHA384, and SHA512.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. CertificateInstalled with certificateType CSMSRootCertificate.

Manual Action: Request the CSMS to send a DeleteCertificateRequest.

2. The CSMS sends a GetInstalledCertificateIdsRequest
3. The Test System responds with a GetInstalledCertificateIdsResponse
    - With status is Accepted
    - certificateHashDataChain contains an entry with following values:
    - certificateHashDataChain[0].certificateType is CSMSRootCertificate
    - certificateHashDataChain[0].certificateHashData.hashAlgorithm is SHA256
4. The CSMS sends a DeleteCertificateRequest
5. The Test System responds with a DeleteCertificateResponse
    - With status is Accepted

Note(s):
- Steps 1 - 5 will be repeated for each hash algorithm (SHA256, SHA384, SHA512).

Tool validations
* Step 2:
    Message: GetInstalledCertificateIdsRequest
    - certificateType contains CSMSRootCertificate OR is omitted.
* Step 4:
    Message: DeleteCertificateRequest
    - certificateHashData is <Returned certificateHashData at Step 3>.

Post scenario validations:
    N/a
"""
