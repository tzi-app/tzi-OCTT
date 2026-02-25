"""
Test case name      Unlock Connector - Unknown Connector
Test case Id        TC_031_CSMS
OCPP Version        1.6J
Profile             Core
Document ref        CompliancyTestTool-TestCaseDocument, Section 3.10.2, Table 148, Page 129/176

Description         This scenario is used to reject an UnlockConnector.req, when an unknown connectorId is given.
                    The Central System (SUT) sends an UnlockConnector.req with a connectorId that does not exist
                    on the Charge Point, and the Charge Point responds with an UnlockConnector.conf indicating
                    that the operation is not supported (status = NotSupported).

Purpose             To test if the Central System is able to handle a Charge Point that does not support
                    UnlockConnector.req.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
1. The Central System (SUT) sends an UnlockConnector.req to the Charge Point.
    Message: UnlockConnector.req
    - connectorId: integer (> 0), an unknown/invalid connector identifier
2. The Charge Point (OCTT) responds with an UnlockConnector.conf.
    Message: UnlockConnector.conf
    - status: "NotSupported"

OCPP 1.6 Message Details:
    UnlockConnector.req (Central System -> Charge Point):
        - connectorId (Required, integer > 0): The identifier of the connector to be unlocked.
    UnlockConnector.conf (Charge Point -> Central System):
        - status (Required, string): "Unlocked" | "UnlockFailed" | "NotSupported"

Tool validations
* Step 2:
    (Message: UnlockConnector.conf)
    status is NotSupported

Expected result(s) / behaviour
    n/a
"""
