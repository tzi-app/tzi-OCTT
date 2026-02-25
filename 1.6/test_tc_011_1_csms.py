"""
Test case name      Remote Start Charging Session – Remote Start First
Test case Id        TC_011_1_CSMS
Chapter             3.4.2 (under 3.4. Core Profile - Remote actions Happy flow)
Protocol            OCPP 1.6J
Document ref        Page 115-116, Table 130
                    (OCPP Compliancy Testing Tool - TestCaseDocument, 2025-11)

System under test   Central System

Description         This scenario is used to start a transaction remotely.

Purpose             To test if the Central System can handle when a Charge point starts a transaction after
                    receiving a RemoteStartTransaction.req from the Central System.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
    1.  The Central System sends a RemoteStartTransaction.req to the Charge Point.
        - idTag: a valid IdToken (e.g. from test configuration)
        - connectorId: (optional) connector to start on
    2.  The Charge Point responds with a RemoteStartTransaction.conf.
        - status: Accepted
    3.  The Charge Point sends an Authorize.req to the Central System.
        - idTag: the same IdToken received in step 1
    4.  The Central System responds with an Authorize.conf.
        - idTagInfo.status: Accepted
    5.  The Charge Point sends a StatusNotification.req to the Central System.
        - connectorId: 1 (or configured connector)
        - errorCode: NoError
        - status: Preparing
    6.  The Central System responds with a StatusNotification.conf (empty body).
    [EV driver plugs in the cable.]
    7.  The Charge Point sends a StartTransaction.req to the Central System.
        - connectorId: 1 (or configured connector)
        - idTag: the same IdToken from step 1
        - meterStart: current meter value in Wh (integer)
        - timestamp: current datetime in ISO 8601 format
    8.  The Central System responds with a StartTransaction.conf.
        - transactionId: integer assigned by Central System
        - idTagInfo.status: Accepted
    9.  The Charge Point sends a StatusNotification.req to the Central System.
        - connectorId: 1 (or configured connector)
        - errorCode: NoError
        - status: Charging
    10. The Central System responds with a StatusNotification.conf (empty body).

Tool validation(s)
    * Step 2:  (Message: RemoteStartTransaction.conf)  status is Accepted
    * Step 4:  (Message: Authorize.conf)  idTagInfo.status is Accepted
              NOTE: Official doc labels this as "Step 6" but Authorize.conf is scenario
              Step 4; appears to be a document error (to be verified).
    * Step 5:  (Message: StatusNotification.req)  status is Preparing
    * Step 8:  (Message: StartTransaction.conf)  idTagInfo.status is Accepted
    * Step 9:  (Message: StatusNotification.req)  status is Charging

Expected result(s) / behaviour
    n/a

Notes
    - Field-level details in scenario steps (idTag, connectorId, meterStart, etc.) are
      inferred from the OCPP 1.6 specification; the official test case document only lists
      message names without field details (to be verified).
"""
