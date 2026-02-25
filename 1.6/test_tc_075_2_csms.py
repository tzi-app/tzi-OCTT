"""
Test case name      Install a certificate on the Charge Point - CentralSystemRootCertificate
Test case Id        TC_075_2_CSMS
Section             3.21.1 Secure connection setup
System under test   Central System
Document ref        Table 187, pp. 160-161 (CompliancyTestTool-TestCaseDocument 2025-11)

Description         The Central System requests the Charge Point to install a new Central System root certificate.

Purpose             To check if the Central System is able to install a certificate on the Charge Point.

Prerequisite(s)     The Central System supports Security profile 2 and/or 3.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    The OCTT requests the Central System to install CentralSystemRootCertificate 2.

    1. The Central System sends an InstallCertificate.req
    2. The Charge Point responds with an InstallCertificate.conf

    3. The Central System sends a GetInstalledCertificateIds.req
    4. The Charge Point responds with a GetInstalledCertificateIds.conf

Tool Validations
    * Step 1:
        (Message: InstallCertificate.req)
        certificateType is CentralSystemRootCertificate
        certificate is <Configured root certificate>

    * Step 2:
        (Message: InstallCertificate.conf)
        status is Accepted

    * Step 3:
        (Message: GetInstalledCertificateIds.req)
        The certificateType is CentralSystemRootCertificate

    * Step 4:
        (Message: GetInstalledCertificateIds.conf)
        The status is Accepted
        certificateHashData is <Includes the certificate information of the installed certificate from step 1.>

    Note: This test case must be executed with a Root CA certificate in order to get the correct response
    message from the OCTT.

Expected result(s) / behaviour: n/a
"""
