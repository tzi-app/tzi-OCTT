"""
Test case name      Unlock connector - no charging session running (Fixed cable)
Test case Id        TC_017_2_CSMS
Test document       CompliancyTestTool-TestCaseDocument, Table 136, page 121/176
OCPP Version        1.6J
Profile             Core
Section             3.6.2 Unlock connector - no charging session running (Fixed cable)
System under test   Central System (CSMS)

Description         This scenario describes how the Charge Point should react to an
                    UnlockConnector.req, when having a fixed cable.

Purpose             To test if the Central System can handle when the Charge Point notifies
                    the Central System that it does not support the unlocking of a connector.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. The Central System sends an UnlockConnector.req to the Charge Point.
       - connectorId: identifier of the connector to unlock
    2. The Charge Point responds with an UnlockConnector.conf.

Tool Validations
    * Step 2 (UnlockConnector.conf):
      - status MUST be "NotSupported"

Expected Result(s) / Behaviour
    Charge Point:   n/a
    Central System: n/a

OCPP 1.6 Messages (reference from OCPP 1.6 spec, not from the test document)
    UnlockConnector.req:
        - connectorId (Required, integer): The identifier of the connector to be unlocked.
    UnlockConnector.conf:
        - status (Required, UnlockStatus): Indicates whether the connector has been unlocked.
          Accepted values: Unlocked, UnlockFailed, NotSupported
"""
