"""
Test case name      Remote Start Charging Session – Time Out
Test case Id        TC_011_2_CSMS
Chapter             3.4. Core Profile - Remote actions Happy flow
Section             3.4.3. Remote Start Charging Session – Time Out
Protocol            OCPP 1.6J
Doc reference       CompliancyTestTool-TestCaseDocument (2025-11), Table 131, Page 116/176

System under test   Central System

Description         This scenario is used to set a connector back to available, after receiving a
                    RemoteStartTransaction.req and it takes too long to plug in the cable.

Purpose             To test if the Central System can handle when a Charge Point sets the connector back to
                    available, after reaching the configured connection timeout.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
    1.  The Central System sends a RemoteStartTransaction.req to the Charge Point.
        - idTag: a valid IdToken (e.g. from test configuration)       [NOTE: field inferred from OCPP 1.6 spec, not in doc]
        - connectorId: (optional) connector to start on               [NOTE: field inferred from OCPP 1.6 spec, not in doc]
    2.  The Charge Point responds with a RemoteStartTransaction.conf.
        - status: Accepted
    3.  The Charge Point sends an Authorize.req to the Central System.
        - idTag: the same IdToken received in step 1                  [NOTE: field inferred from OCPP 1.6 spec, not in doc]
    4.  The Central System responds with an Authorize.conf.
        - idTagInfo.status: Accepted
    5.  The Charge Point sends a StatusNotification.req to the Central System.
        - connectorId: 1 (or configured connector)                    [NOTE: field inferred from OCPP 1.6 spec, not in doc]
        - errorCode: NoError                                          [NOTE: field inferred from OCPP 1.6 spec, not in doc]
        - status: Preparing
    6.  The Central System responds with a StatusNotification.conf.
    [After the configured connection timeout has been reached.]
    7.  The Charge Point sends a StatusNotification.req to the Central System.
        - connectorId: 1 (or configured connector)                    [NOTE: field inferred from OCPP 1.6 spec, not in doc]
        - errorCode: NoError                                          [NOTE: field inferred from OCPP 1.6 spec, not in doc]
        - status: Available
    8.  The Central System responds with a StatusNotification.conf.

Tool validation(s)
    * Step 2:  (Message: RemoteStartTransaction.conf)  status is Accepted
    * Step 4:  (Message: Authorize.conf)  idTagInfo.status is Accepted
    * Step 5:  (Message: StatusNotification.req)  status is Preparing
    * Step 7:  (Message: StatusNotification.req)  status is Available

Expected result(s) / behaviour
    n/a
"""
