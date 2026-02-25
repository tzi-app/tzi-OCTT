"""
Test case name      Remote Start Charging Session – Cable Plugged in First
Test case Id        TC_010_CSMS
Table               129
Page                115/176
Chapter             3.4. Core Profile - Remote actions Happy flow
Section             3.4.1. Remote Start Charging Session – Cable Plugged in First
Protocol            OCPP 1.6J

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
    [EV driver plugs in the cable.]
    1.  The Charge Point sends a StatusNotification.req
    2.  The Central System responds with a StatusNotification.conf
    3.  The Central System sends a RemoteStartTransaction.req
    4.  The Charge Point responds with a RemoteStartTransaction.conf
    5.  The Charge Point sends an Authorize.req
    6.  The Central System responds with an Authorize.conf
    7.  The Charge Point sends a StartTransaction.req
    8.  The Central System responds with a StartTransaction.conf
    9.  The Charge Point sends a StatusNotification.req
    10. The Central System responds with a StatusNotification.conf

Tool validation(s)
    * Step 1:  (Message: StatusNotification.req)  status is Preparing
    * Step 4:  (Message: RemoteStartTransaction.conf)  status is Accepted
    * Step 6:  (Message: Authorize.conf)  idTagInfo.status is Accepted
    * Step 8:  (Message: StartTransaction.conf)  idTagInfo.status is Accepted
    * Step 9:  (Message: StatusNotification.req)  status is Charging

Expected result(s) / behaviour
    n/a

Notes (to be fixed later)
    - The official doc scenario only lists message names per step. Field-level details
      (connectorId, errorCode, idTag, meterStart, timestamp, transactionId, etc.) need
      to be inferred from the OCPP 1.6 specification and verified against actual OCTT behavior.
    - The official doc does not specify which idTag value should be used in step 3
      (RemoteStartTransaction.req) or whether connectorId is required/optional.
    - The official doc does not specify the exact fields expected in StartTransaction.req (step 7).
"""
