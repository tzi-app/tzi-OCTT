"""
Test case name      Trigger Message - Rejected
Test case Id        TC_055_CSMS
Feature profile     Remote Trigger
Reference           CompliancyTestTool-TestCaseDocument, Section 3.18.2, Table 177, Pages 150-151

Description         The Central System triggers a message from the Charge Point, but the Charge Point
                    rejects the message.

Purpose             To check whether the Central System is able to handle a reject on a triggered message.

Prerequisite(s)     The Central System supports the Remote Trigger feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
1.  The Central System sends a TriggerMessage.req with:
        - requestedMessage = MeterValues
2.  The Charge Point responds with a TriggerMessage.conf with:
        - status = Rejected

Tool validations
* Step 1:
    (Message: TriggerMessage.req)
    - requestedMessage should be MeterValues
* Step 2:
    (Message: TriggerMessage.conf)
    - status is Rejected

Expected result(s)
    The Central System processes the response from the Charge Point.
"""
