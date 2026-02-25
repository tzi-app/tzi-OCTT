"""
Test case name      Remote Stop Charging Session
Test case Id        TC_012_CSMS
Chapter             3.4.4 Core Profile - Remote actions Happy flow
Table               Table 132
Page                117-118/176
Protocol            OCPP 1.6J

System under test   Central System

Description         This scenario is used to remotely stop a transaction.

Purpose             To test if the Central System can remotely stop a transaction.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      Charging (Table 201 - simulates CP starting a transaction;
                            itself requires Reusable State: Authorized)

Test Scenario
    1.  The Central System sends a RemoteStopTransaction.req to the Charge Point.
    2.  The Charge Point responds with a RemoteStopTransaction.conf.
    3.  The Charge Point sends a StopTransaction.req to the Central System.
    4.  The Central System responds with a StopTransaction.conf.
    5.  The Charge Point sends a StatusNotification.req to the Central System.
    6.  The Central System responds with a StatusNotification.conf.
    [EV driver unplugs the cable.]
    7.  The Charge Point sends a StatusNotification.req to the Central System.
    8.  The Central System responds with a StatusNotification.conf.

Tool validation(s)
    * Step 2:  (Message: RemoteStopTransaction.conf)  status is Accepted
    * Step 3:  (Message: StopTransaction.req)  reason is Remote
    * Step 5:  (Message: StatusNotification.req)  status is Finishing
    * Step 7:  (Message: StatusNotification.req)  status is Available

Expected result(s) / behaviour
    n/a
"""
