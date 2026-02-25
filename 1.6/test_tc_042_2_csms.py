"""
Test case name      Get Local List Version (empty)
Test case Id        TC_042_2_CSMS
System under test   Central System
Document reference  Table 156, page 135/176

Description         The Central System can request a Charge Point for the version number of the
                    Local Authorization List.

Purpose             Check whether a Central System is able to retrieve the local list version from
                    a Charge Point.

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    Charge Point (Tool)                          Central System (SUT)
    2. The Charge Point responds with a          1. The Central System sends a
       GetLocalListVersion.conf.                    GetLocalListVersion.req.

Tool validations
    Charge Point (Tool):
        * Step 2: (Message: GetLocalListVersion.conf)
            - listVersion is 0
    Central System (SUT):
        * Step 1: n/a

Expected result(s) / behaviour
    n/a
"""
