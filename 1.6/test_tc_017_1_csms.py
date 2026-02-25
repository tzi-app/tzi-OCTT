"""
Test case name      Unlock connector - no charging session running (Not fixed cable)
Test case Id        TC_017_1_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.6.1 Core Profile - Unlocking Happy Flow
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument, Table 135, Page 126

Description         This scenario is used to unlock a connector of a Charge Point.

Purpose             To test if the Central System can handle when the Charge Point unlocks
                    the connector, when requested by the Central System.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    Charge Point (Tool)                         Central System (SUT)
    -----------------------------------------   -----------------------------------------
                                                1. The Central System sends a
                                                   UnlockConnector.req
    2. The Charge Point responds with a
       UnlockConnector.conf

Tool Validations
    Charge Point (Tool):
        * Step 2 (Message: UnlockConnector.conf):
          - status is "Unlocked"
    Central System (SUT):
        n/a

Expected result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): n/a

OCPP 1.6 Messages
    UnlockConnector.req:
        - connectorId (Required, integer): The identifier of the connector to be unlocked.
    UnlockConnector.conf:
        - status (Required, UnlockStatus): Indicates whether the connector has been unlocked.
          Accepted values: Unlocked, UnlockFailed, NotSupported
"""
