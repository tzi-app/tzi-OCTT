"""
Reusable State      InstalledCertificatesReceived
OCPP version        1.6J (Security Extension)
System under test   Central System (SUT)
Document ref        CompliancyTestTool-TestCaseDocument-CSMS-Section3, Section 3.22, Table 202, pages 174-175

Description         This state will simulate that the CPO requests the installed root
                    certificates on the Charge Point.

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
    - <Expected certificateType> is unresolved; the actual expected value
      depends on the test case that invokes this reusable state.
"""
