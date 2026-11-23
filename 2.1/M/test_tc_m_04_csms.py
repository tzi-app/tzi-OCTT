"""
Test case name      Install CA certificate - MORootCertificate
Test case Id        TC_M_04_CSMS
Use case Id(s)      M05
Requirement(s)      M05.FR.01

Requirement Details:
    M05.FR.01: The Charging Station SHALL attempt to install the certificate and respond with an
               InstallCertificateResponse.
        Precondition: After receiving an InstallCertificateRequest
System under test   CSMS

Description         The CSMS is able to request the Charging Station to install new Root CA certificates using
                    the InstallCertificateRequest message.

Purpose             To verify if the CSMS is able to request a Charging Station to install a new
                    MORootCertificate.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State CertificateInstalled for certificateType MORootCertificate

Tool validations
N/a

Post scenario validations:
    N/a
"""
