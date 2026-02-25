"""
Test case name      Delete a specific certificate from the Charge Point
Test case Id        TC_076_CSMS
Section             3.21.1 Secure connection setup
Reference           Table 188, pages 160-161 (CompliancyTestTool-TestCaseDocument 2025-11)
System under test   Central System

Description         To facilitate the management of the Charge Point's installed certificates, a method of deleting an installed
                    certificate is provided. The Central System requests the Charge Point to delete a specific certificate.

Purpose             To check if the Central System is able to delete an installed certificate from the Charge Point.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    The OCTT requests the Central System to install CentralSystemRootCertificate 2.

    1. The Central System sends an InstallCertificate.req
    2. The Charge Point responds with an InstallCertificate.conf

    The OCTT requests the Central System to delete the just installed CentralSystemRootCertificate 2.

    3. The Central System sends a GetInstalledCertificateIds.req
    4. The Charge Point responds with a GetInstalledCertificateIds.conf

        Note(s): The Central System sends a GetInstalledCertificateIds.req to confirm the hashAlgorithm
        it needs to use for requesting the deletion of the Root certificate.

    5. The Central System sends a DeleteCertificate.req
    6. The Charge Point responds with a DeleteCertificate.conf

    7. The Central System optionally sends a GetInstalledCertificateIds.req
    8. The Charge Point responds with a GetInstalledCertificateIds.conf

        Note(s): This step is optional. It is only used for the Central System to confirm the Root
        certificate actually has been deleted.

    Note(s):
    - Steps 1 - 8 will be repeated for each hash algorithm (SHA256, SHA384, SHA512).

Tool Validations
    * Step 4:
        (Message: GetInstalledCertificateIds.conf)
        status is Accepted
        certificateHashData.hashAlgorithm is <For each hash algorithm; (SHA256, SHA384, SHA512)>

    * Step 5:
        (Message: DeleteCertificate.req)
        hashAlgorithm is <Configured HashAlgorithm> (It needs to be equal to the hashAlgorithm returned at step 4)
        certificateHashData is <Includes the certificate information of the installed CentralSystemRootCertificate.>
        The individual fields of the certificateHashData are verified by the OCTT (the OCTT compares these with
        its own certificateHashData calculation).

    * Step 6:
        (Message: DeleteCertificate.conf)
        status is Accepted

Expected result(s) / behaviour: n/a
"""
