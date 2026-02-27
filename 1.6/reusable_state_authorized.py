"""
Reusable State      Authorized
OCPP version        1.6J
System under test   Central System (CS)
Document reference  Section 3.22, Table 200 (pages 173-174/176) in
                    CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf

Description         This state will simulate that the EV Driver is locally authorizing to start
                    a transaction on the simulated Charge Point.

Before (Preparations):
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Scenario Detail(s):
    Charge Point (Tool)                          | Central System (SUT)
    1. The Charge Point sends an Authorize.req   | 2. The Central System responds with an
       - idTag is <Configured Valid IdTag>       |    Authorize.conf

Tool validation(s):
    * Step 2:
        (Message: Authorize.conf)
        - idTagInfo.status should be Accepted

Expected result(s) / behaviour:
    State is Authorized.
"""
