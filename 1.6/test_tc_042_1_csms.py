"""
Test case name      Get Local List Version (not supported)
Test case Id        TC_042_1_CSMS
System under test   Central System
Reference           Section 3.14.1, Table 155, Page 135 (CompliancyTestTool-TestCaseDocument)

Description         The Central System can request a Charge Point for the version number of the Local
                    Authorization List.

Purpose             Check whether a Central System is able to retrieve the local list version from a
                    Charge Point.

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
1. The Central System sends a GetLocalListVersion.req to the Charge Point.
2. The Charge Point responds with a GetLocalListVersion.conf.

Tool validations
    * Step 1: (Message: GetLocalListVersion.req)
        - n/a
    * Step 2: (Message: GetLocalListVersion.conf)
        - listVersion is -1

Expected result(s) / behaviour
    - n/a
"""
