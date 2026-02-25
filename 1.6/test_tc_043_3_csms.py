"""
Test case name      Send Local Authorization List - Failed
Test case Id        TC_043_3_CSMS
System under test   Central System (SUT)
Reference           CompliancyTestTool-TestCaseDocument, Table 158, Page 136

Description         The Charge Point can authorize an EV driver based on a local list that is set by
                    the Central System.

Purpose             To check whether a Central System can handle a Rejected status, after sending a
                    Local Authorization List.
                    NOTE: The official doc says "Rejected" in Purpose but "Failed" in Tool
                    validations and Expected results. Likely a doc typo - should be "Failed".

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
1. The Central System sends a SendLocalList.req.
2. The Charge Point responds with a SendLocalList.conf.

Tool validations
    * Step 1: (Message: SendLocalList.req)
        - updateType should be Full.
    * Step 2: (Message: SendLocalList)
        - Status is Failed.

Expected result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): The Central System is able to send a local list and is able to receive a
    Failed response.
"""
