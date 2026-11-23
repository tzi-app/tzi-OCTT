"""
Test case name      Install CA certificate - Failed
Test case Id        TC_M_05_CSMS
Use case Id(s)      M05
Requirement(s)      M05.FR.01, M05.FR.03

Requirement Details:
    M05.FR.01: The Charging Station SHALL attempt to install the certificate and respond with an
               InstallCertificateResponse.
        Precondition: After receiving an InstallCertificateRequest
    M05.FR.03: The Charging Station SHALL indicate failure by setting status to Failed in the
               InstallCertificateResponse.
        Precondition: M05.FR.01 AND The installation failed
System under test   CSMS

Description         The CSMS is able to request the Charging Station to install new Root CA certificates using
                    the InstallCertificateRequest message.

Purpose             To verify if the CSMS is able to handle a Charging Station reporting it failed to install
                    the requested certificate.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send an InstallCertificateRequest with certificateType CSMSRootCertificate.

1. The CSMS sends a InstallCertificateRequest
2. The Test System responds with a InstallCertificateResponse
    With status is Failed

Tool validations
* Step 1:
    Message: InstallCertificateRequest
    certificateType must be CSMSRootCertificate
    certificate contains <A certificate>

Post scenario validations:
    N/a
"""
