"""
Test case name      Unlock Connector - With Charging Session (Not fixed cable)
Test case Id        TC_018_1_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.6. Core Profile - Unlocking Happy flow
                    3.6.3. Unlock Connector - With Charging Session
System under test   Central System (SUT)

Reference           CompliancyTestTool-TestCaseDocument (2025-11), Table 137, Page 122

Description         This scenario is used to unlock a connector of a Charge Point, while a
                    transaction is ongoing.

Purpose             To test if the Central System can handle when the Charge Point unlocks
                    the connector, when requested by the Central System.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): Charging

Reusable State: Charging (Table 201, Page 174)
    Description: Simulates the Charge Point starting a transaction.
    Prerequisite: Authorized reusable state (Table 200, Page 173)

    Authorized state (Table 200, Page 173):
        No prerequisites.
        1. CP sends Authorize.req (idTag = <Configured Valid IdTag>)
        2. CS responds Authorize.conf
        Validation: Step 2 - idTagInfo.status should be Accepted
        Expected result: State is Authorized

    Charging state (Table 201, Page 174):
        Prerequisite: Authorized
        1. CP sends StatusNotification.req (status=Preparing, connectorId=<Configured ConnectorId>)
        2. CS responds StatusNotification.conf
        3. CP sends StartTransaction.req (idTag=<Configured Valid IdTag>, connectorId=<Configured ConnectorId>)
        4. CS responds StartTransaction.conf
        5. CP sends StatusNotification.req (status=Charging, connectorId=<Configured ConnectorId>)
        6. CS responds StatusNotification.conf
        Validation: Step 4 - idTagInfo.status should be Accepted
        Expected result: State is Charging

Test Scenario
    Charge Point (Tool)                           Central System (SUT)
    1.                                            The Central System sends a UnlockConnector.req
    2. The Charge Point responds with a
       UnlockConnector.conf
    3. The Charge Point sends a
       StatusNotification.req                     4. The Central System responds with a
                                                     StatusNotification.conf
    5. The Charge Point sends a
       StopTransaction.req                        6. The Central System responds with a
                                                     StopTransaction.conf
    [EV driver unplugs the cable.]
    7. The Charge Point sends a
       StatusNotification.req                     8. The Central System responds with a
                                                     StatusNotification.conf

Tool Validations
    * Step 2 (UnlockConnector.conf):
      - status is Unlocked
    * Step 3 (StatusNotification.req):
      - status is Finishing
    * Step 5 (StopTransaction.req):
      - reason is UnlockCommand
    * Step 7 (StatusNotification.req):
      - status is Available

Expected result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): n/a

OCPP 1.6 Messages
    UnlockConnector.req:
        - connectorId (Required, integer): The identifier of the connector to be unlocked.
    UnlockConnector.conf:
        - status (Required, UnlockStatus): Indicates whether the connector has been unlocked.
          Accepted values: Unlocked, UnlockFailed, NotSupported
    StatusNotification.req:
        - connectorId (Required, integer): The id of the connector.
        - errorCode (Required, ChargePointErrorCode): The error code reported by the CP.
        - status (Required, ChargePointStatus): The current status of the connector.
          Relevant values: Finishing, Available
    StatusNotification.conf:
        - (empty payload)
    StopTransaction.req:
        - meterStop (Required, integer): Meter value in Wh at stop.
        - timestamp (Required, dateTime): Time at which the transaction was stopped.
        - transactionId (Required, integer): The transaction id as provided by StartTransaction.conf.
        - reason (Optional, Reason): Reason for stopping the transaction.
          Expected value: UnlockCommand
    StopTransaction.conf:
        - idTagInfo (Optional, IdTagInfo): Contains status info about the identifier.
"""
