"""
Test case name      Cold Boot Charge Point
Test case Id        TC_001_CSMS
OCPP Version        1.6
Chapter             3.1 - Cold Boot Charge Point
Section             3.1.1
System under test   Central System
PDF Reference       CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, Page 110, Table 122
Doc Reference       CompliancyTestTool-TestCaseDocument.html, Page 110/176, Table 122

Description         This scenario is used to startup the Charge Point and let it register itself
                    at the Central System.

Purpose             To test if the Central System is able to handle a boot process.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Scenario Detail(s)
    Charge Point (Tool)                              Central System (SUT)
    ─────────────────────────────────────────────────────────────────────────────
    1. The Charge Point sends a                       2. The Central System responds with a
       BootNotification.req                              BootNotification.conf

    [Send a StatusNotification per connector
     and connectorId=0.]
    3. The Charge Point sends a                       4. The Central System responds with a
       StatusNotification.req                            StatusNotification.conf

    [Every x seconds.]
    5. The Charge Point sends a                       6. The Central System responds with a
       Heartbeat.req                                     Heartbeat.conf

Tool Validations
    Charge Point (Tool):
        * Step 1:
          (Message: BootNotification.req)
        * Step 3:
          (Message: StatusNotification.req)
          - status is Available
        * Step 5:
          (Message: Heartbeat.req)
          Send a Heartbeat.req every x seconds. x equals interval from step 2.

    Central System (SUT):
        * Step 2:
          (Message: BootNotification.conf)
          - The status is Accepted

Expected Result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): n/a

OCPP 1.6 Messages Used:
    - BootNotification.req / BootNotification.conf
    - StatusNotification.req / StatusNotification.conf
    - Heartbeat.req / Heartbeat.conf

Key Fields (supplementary - from OCPP 1.6 spec, not from test case document):
    BootNotification.req:
        - chargePointVendor (String, required, max 20 chars)
        - chargePointModel (String, required, max 20 chars)
        - chargePointSerialNumber (String, optional, max 25 chars)
        - chargeBoxSerialNumber (String, optional, max 25 chars)
        - firmwareVersion (String, optional, max 50 chars)
        - iccid (String, optional, max 20 chars)
        - imsi (String, optional, max 20 chars)
        - meterType (String, optional, max 25 chars)
        - meterSerialNumber (String, optional, max 25 chars)

    BootNotification.conf:
        - status (RegistrationStatus: Accepted | Pending | Rejected)
        - currentTime (dateTime, required)
        - interval (Integer, required - heartbeat interval in seconds)

    StatusNotification.req:
        - connectorId (Integer, required, >= 0; 0 = Charge Point main controller)
        - errorCode (ChargePointErrorCode, required)
        - status (ChargePointStatus: Available | Preparing | Charging | SuspendedEVSE |
                  SuspendedEV | Finishing | Reserved | Unavailable | Faulted)
        - timestamp (dateTime, optional)

    StatusNotification.conf:
        - (empty payload)

    Heartbeat.req:
        - (empty payload)

    Heartbeat.conf:
        - currentTime (dateTime, required)
"""
