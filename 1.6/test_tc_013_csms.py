"""
Test case name      Hard Reset
Test case Id        TC_013_CSMS
Table               133
Document ref        Page 119 of 176 (CompliancyTestTool-TestCaseDocument, 2025-11)
Section             3.5.1 - Core Profile - Resetting Happy Flow
System under test   Central System (SUT)

Description         This scenario is used to hard reset a Charge Point.
Purpose             To test if the Central System is able to trigger a hard reset.

Prerequisite(s)     n/a
Before
    Configuration State(s):  n/a
    Memory State(s):         n/a
    Reusable State(s):       n/a

Scenario Detail(s)
    Charge Point (Tool)                          Central System (SUT)
    2. CP responds with Reset.conf               1. CS sends a Reset.req
    3. CP sends a BootNotification.req           4. CS responds with BootNotification.conf
    [Send per connector and connectorId=0.]      6. CS responds with StatusNotification.conf
    5. CP sends a StatusNotification.req

Tool validation(s)
    Charge Point (Tool):
    - Step 2: (Message: Reset.conf) status is Accepted
    - Step 5: (Message: StatusNotification.req) status is Available
    Central System (SUT):
    - Step 1: (Message: Reset.req) type is Hard
    - Step 4: (Message: BootNotification.conf) status is Accepted

Expected result(s) / behaviour    n/a
"""
