"""
Reusable State      InstalledCertificatesReceived
State Id            RS_INSTALLED_CERTIFICATES_RECEIVED
OCPP version        1.6J (Security Extension)
System under test   Central System (CS)
Document ref        CompliancyTestTool-TestCaseDocument, Table 202, pages 174-175

Description         This state will simulate that the CPO requests the installed root
                    certificates on the Charge Point.

Purpose             To bring the system into a known state where the Central System has received
                    information about which root certificates are currently installed on the
                    Charge Point.

Before (Preparations):
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Scenario
    Manual Action: Request installed root certificates.
1. The Central System sends a GetInstalledCertificateIds.req.
2. The Charge Point responds with a GetInstalledCertificateIds.conf with:
   - certificateHashData = <Calculated hash data>

Tool validations:
    * Step 1:
        (Message: GetInstalledCertificateIds.req)
        - certificateType should be <Expected certificateType>

Expected result(s) / behaviour:
    State is InstalledCertificatesReceived.

Notes (to be fixed later):
    - State Id "RS_INSTALLED_CERTIFICATES_RECEIVED" is not explicitly shown in
      the document table; it may come from the OCTT tool internals.
    - "OCPP version" and "System under test" fields are not shown as explicit
      table columns in the document; inferred from the test context.
    - "Purpose" section is not in the official table; added for clarity.
    - <Expected certificateType> is unresolved; the actual expected value
      depends on the test case that invokes this reusable state.
"""
