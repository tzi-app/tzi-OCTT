"""
Test case name      Invalid CentralSystemCertificate Security Event
Test case Id        TC_078_CSMS
Table               190 (page 163/176 of CompliancyTestTool-TestCaseDocument)
Section             3.21.2 Security event/logging
System under test   Central System

Description         The Charge Point notifies the Central System of an invalid certificate.

Purpose             To check if the Central System can handle it when a Charge Point registers a security event and notifies the
                    Central System about it.

Prerequisite(s)     The Central System supports Security profile 2 and/or 3.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1. The Central System sends an InstallCertificate.req
    2. The Charge Point responds with an InstallCertificate.conf

    3. The Charge Point sends a SecurityEventNotification.req
    4. The Central System responds with a SecurityEventNotification.conf

Tool Validations
    * Step 1:
        (Message: InstallCertificate.req)
        certificateType is CentralSystemRootCertificate
        certificate is <Configured certificate>

        Note: For this testcase the OCTT will reject any certificate.

    * Step 2:
        (Message: InstallCertificate.conf)
        status is Rejected

    * Step 3:
        (Message: SecurityEventNotification.req)
        The type is InvalidCentralSystemCertificate

Expected result(s) / behaviour: n/a
"""
