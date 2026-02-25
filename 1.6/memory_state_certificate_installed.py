"""
Memory State        CertificateInstalled
State Id            MS_CERTIFICATE_INSTALLED
OCPP version        1.6J (Security Extension)
System under test   Central System (CS)
Document Reference  Page 175, Table 203 (CompliancyTestTool-TestCaseDocument, 2025-11)

Description         This state installs a root certificate on the Charge Point.

Purpose             To bring the system into a known state where a specific root certificate has
                    been installed on the Charge Point by the Central System.
                    TODO: "Purpose" field is not present in the document table — verify source.

Before (Preparations):
    Configuration State(s): N/a
    Memory State(s): N/a
    Reusable State(s): N/a

Scenario
    [Only send if the certificate is not already installed]
1. The Central System sends an InstallCertificate.req.
   TODO: Document does not list field details for this request. The following are
   inferred from the OCPP 1.6 Security Extension spec — to be verified:
   - certificateType = <Certificate type to install>
     (e.g., CentralSystemRootCertificate or ManufacturerRootCertificate)
   - certificate = <PEM-encoded certificate data>
2. The Charge Point responds with an InstallCertificate.conf.

Tool validations:
    * Step 2:
        (Message: InstallCertificate.conf)
        - status should be Accepted

Expected result(s) / behaviour:
    State is CertificateInstalled.
"""
