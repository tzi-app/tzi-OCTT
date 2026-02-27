"""
Memory State        CertificateInstalled
State Id            MS_CERTIFICATE_INSTALLED
OCPP version        1.6J (Security Extension)
System under test   Charge Point (SUT)
Document Reference  Page 107, Table 119 (CompliancyTestTool-TestCaseDocument-CSMS-Section3, 2025-11)

Description         This state will ensure that a root certificate is installed on the Charge Point.

Before (Preparations):
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Scenario
                        Charge Point (SUT)                          Central System (Tool)
                        --------------------------                  --------------------------
                        2. The Charge Point responds with a         1. The Central System sends a
                           GetInstalledCertificateIds.conf              GetInstalledCertificateIds.req

                        4. The Charge Point responds with a         [Only send if the certificate is not already installed]
                           InstallCertificate.conf                  3. The Central System sends a
                                                                        InstallCertificate.req

Tool validations:
    * Step 2:
        (Message: GetInstalledCertificateIds.conf)
        - status should be Accepted
    * Step 4:
        (Message: InstallCertificate.conf)
        - status should be Accepted

Expected result(s) / behaviour:
    State is CertificateInstalled.

Notes:
    - TODO: Document does not specify field details for GetInstalledCertificateIds.req or
      InstallCertificate.req (e.g., certificateType, certificate PEM data). These must be
      inferred from the OCPP 1.6 Security Extension spec — to be verified.
"""
