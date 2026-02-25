"""
Test case name      Start Charging Session Lock Failure
Test case Id        TC_024_CSMS
System under test   Central System
OCPP version        1.6J

Document reference  CompliancyTestTool-TestCaseDocument (2025-11)
                    Section 3.8.4, Table 144, Page 127/176

Description         This scenario is used to report a connector lock failure.

Purpose             To test if the Central System is able to handle a report of a connector lock failure.

Prerequisite(s)     n/a

Before State(s)
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      Authorized
                            NOTE: "Authorized" is a reusable state reference - exact precondition
                            steps to be verified (to be fixed later).

Test Scenario
1. The Charge Point sends a StatusNotification.req to the Central System.
   - Message: StatusNotification.req
   - connectorId: > 0 (a valid connector)
   - errorCode: NoError
   - status: Preparing
2. The Central System responds with a StatusNotification.conf.
   - Message: StatusNotification.conf (empty payload)
3. [EV driver plugs in the cable.]
   The Charge Point sends a StatusNotification.req to the Central System.
   - Message: StatusNotification.req
   - connectorId: > 0 (same connector as step 1)
   - errorCode: ConnectorLockFailure
   - status: Faulted
4. The Central System responds with a StatusNotification.conf.
   - Message: StatusNotification.conf (empty payload)

Expected result(s) / behaviour
    Charge Point:   n/a
    Central System: n/a

Tool validations
* Step 1:
    (Message: StatusNotification.req)
    - status MUST be "Preparing"
* Step 3:
    (Message: StatusNotification.req)
    - errorCode MUST be "ConnectorLockFailure"
    - status MUST be "Faulted"

OCPP 1.6 Message Details
    StatusNotification.req:
        connectorId (integer, >= 0): The id of the connector for which the status is reported.
            0 = Charge Point main controller.
        errorCode (ChargePointErrorCode): ConnectorLockFailure | EVCommunicationError |
            GroundFailure | HighTemperature | InternalError | LocalListConflict | NoError |
            OtherError | OverCurrentFailure | OverVoltage | PowerMeterFailure |
            PowerSwitchFailure | ReaderFailure | ResetFailure | UnderVoltage | WeakSignal
        status (ChargePointStatus): Available | Preparing | Charging | SuspendedEVSE |
            SuspendedEV | Finishing | Reserved | Unavailable | Faulted
        timestamp (optional, dateTime)
        info (optional, string, max 50 chars)
        vendorId (optional, string, max 255 chars)
        vendorErrorCode (optional, string, max 50 chars)
    StatusNotification.conf:
        (empty - no fields)
"""
