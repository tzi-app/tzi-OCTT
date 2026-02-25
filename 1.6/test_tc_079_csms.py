"""
Test case name      Get Security Log
Test case Id        TC_079_CSMS
Section             3.21.2 Security event/logging
System under test   Central System
Reference           CompliancyTestTool-TestCaseDocument, Table 191, Page 164

Description         The Charge Point uploads a security log to a specified location based on a request of the Central System.

Purpose             To check whether Central System can trigger a Charge Point to upload its security log.

Prerequisite(s)     The Central System supports a security profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a GetLog.req
    2. The Charge Point responds with a GetLog.conf

    [The Charge Point starts uploading the security log.]
    3. The Charge Point sends a LogStatusNotification.req
    4. The Central System responds with a LogStatusNotification.conf

    [The Charge Point has finished uploading the security log.]
    5. The Charge Point sends a LogStatusNotification.req
    6. The Central System responds with a LogStatusNotification.conf

Tool Validations
    * Step 1:
        (Message: GetLog.req)
        The log.remoteLocation is <Configured log location>
        The logType is SecurityLog

    * Step 2:
        (Message: GetLog.conf)
        The status is Accepted

    * Step 3:
        (Message: LogStatusNotification.req)
        The status is Uploading

    * Step 5:
        (Message: LogStatusNotification.req)
        The status is Uploaded

Expected result(s) / behaviour: n/a
"""
