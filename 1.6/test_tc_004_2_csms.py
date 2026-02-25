"""
Test case name      Regular Charging Session – Identification First - ConnectionTimeOut
Test case Id        TC_004_2_CSMS
OCPP Version        1.6j
Document Reference  Table 125, page 111/176 (CompliancyTestTool-TestCaseDocument, 2025-11)
Chapter             3.2.3
System under test   Central System

Description         This scenario is used to make a connector available when it is not used.

Purpose             To test if the Central System can handle when the Charge Point sets the
                    connector back to Available, when the connectionTimeOut is reached.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      Authorized (Table 200, page 173/176)
        Definition: CP sends Authorize.req with idTag = <Configured Valid IdTag>,
        CS responds with Authorize.conf where idTagInfo.status should be Accepted.
        NOTE: <Configured Valid IdTag> - exact value to be configured (TBD).

Test Scenario
1. The Charge Point sends a StatusNotification.req
2. The Central System responds with a StatusNotification.conf
   [After the configured connectionTimeOut has expired.]
3. The Charge Point sends a StatusNotification.req
4. The Central System responds with a StatusNotification.conf

Tool Validations
    * Step 1 (Message: StatusNotification.req):
        - status is Preparing
    * Step 3 (Message: StatusNotification.req):
        - status is Available

Expected Result(s)  n/a

OCPP 1.6 Messages Used:
    - StatusNotification.req / StatusNotification.conf

Key Fields:
    StatusNotification.req:
        - connectorId (Integer, required, >= 0; 0 = Charge Point main controller)
        - errorCode (ChargePointErrorCode, required; e.g. NoError)
        - status (ChargePointStatus: Available | Preparing | Charging | SuspendedEVSE |
                  SuspendedEV | Finishing | Reserved | Unavailable | Faulted)
        - timestamp (dateTime, optional)

    StatusNotification.conf:
        - (empty payload)

Configuration Keys:
    - ConnectionTimeOut (Integer, seconds): The time in seconds after which the Charge Point
      will revert to Available if no cable is plugged in after authorization. This is a
      standard OCPP 1.6 configuration key that can be read/set via GetConfiguration /
      ChangeConfiguration.
"""
