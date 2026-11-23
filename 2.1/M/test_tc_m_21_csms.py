"""
Test case name      Delete a certificate from a Charging Station - Failed
Test case Id        TC_M_21_CSMS
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
                    the DeleteCertificateRequest message.

Purpose             To verify if CSMS is able to handle a Charging Station that fails to delete an installed
                    certificate.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   CertificateInstalled with certificateType CSMSRootCertificate.

Test Scenario
Manual Action: Request the CSMS to send a DeleteCertificateRequest.

1. The CSMS sends a GetInstalledCertificateIdsRequest
2. The Test System responds with a GetInstalledCertificateIdsResponse
    - With status is Accepted
    - certificateHashDataChain contains an entry with following values:
    - certificateHashDataChain[0].certificateType is CSMSRootCertificate
    - certificateHashDataChain[0].certificateHashData.hashAlgorithm is SHA256
3. The CSMS sends a DeleteCertificateRequest
4. The Test System responds with a DeleteCertificateResponse
    - With status is Failed

Tool validations
* Step 1:
    Message: GetInstalledCertificateIdsRequest
    - certificateType contains CSMSRootCertificate OR is omitted.
* Step 3:
    Message: DeleteCertificateRequest
    - certificateHashData contains <Returned certificateHashData at Step 2>.

Post scenario validations:
    N/a
"""
