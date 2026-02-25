"""
Test case name      Unlock Connector – Unlock Failure
Test case Id        TC_030_CSMS
OCPP Version        1.6J
Profile             Core
Document ref        CompliancyTestTool-TestCaseDocument, Table 147, Section 3.10.1, Page 134

Description         This scenario is used to report a connector lock failure. The Central System (SUT) sends an
                    UnlockConnector.req to the Charge Point, and the Charge Point responds with an
                    UnlockConnector.conf indicating that the unlock operation failed (status = UnlockFailed).

Purpose             To test if the Central System is able to handle a report of a connector lock failure.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
1. The Central System (SUT) sends an UnlockConnector.req to the Charge Point.
    Message: UnlockConnector.req
    - connectorId: integer (> 0), identifies the connector to unlock
2. The Charge Point (OCTT) responds with an UnlockConnector.conf.
    Message: UnlockConnector.conf
    - status: "UnlockFailed"

OCPP 1.6 Message Details:
    UnlockConnector.req (Central System -> Charge Point):
        - connectorId (Required, integer > 0): The identifier of the connector to be unlocked.
    UnlockConnector.conf (Charge Point -> Central System):
        - status (Required, string): "Unlocked" | "UnlockFailed" | "NotSupported"

Tool validations
* Step 2:
    (Message: UnlockConnector.conf)
    status is UnlockFailed

Expected result(s) / behaviour
    n/a
"""
