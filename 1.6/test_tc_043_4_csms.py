"""
Test case name      Send Local Authorization List - Full
Test case Id        TC_043_4_CSMS
System under test   Central System
Reference           CompliancyTestTool-TestCaseDocument 2025-11, Table 159, p.136-137/176

Description         The Charge Point can authorize an EV driver based on a local list that is set by
                    the Central System. In this scenario, the Central System sends a full local
                    authorization list to the Charge Point, which accepts it.
                    NOTE: The second sentence above is not in the official document but is an
                    accurate clarification of the test intent.

Purpose             Check whether a Local Authorization List can be sent to a Charge Point to
                    authorize an EV driver.

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile and
                    has at least 1 IdToken to add to the local authorization list.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
1. The Central System sends a SendLocalList.req to the Charge Point.
2. The Charge Point responds with a SendLocalList.conf.

Tool validations
    * Step 1: (Message: SendLocalList.req)
        - UpdateType should be Full.
        - All localAuthorizationList entries have an idTagInfo.
    * Step 2: (Message: SendLocalList.conf)
        - status is Accepted.

Expected result(s) / behaviour
    The Central System is able to send a local list.
"""
