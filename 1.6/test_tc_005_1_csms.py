"""
Test case name      EV Side Disconnected - StopTransactionOnEVSideDisconnect = true -
                    UnlockConnectorOnEVSideDisconnect = true
Test case Id        TC_005_1_CSMS
OCPP Version        1.6j
Chapter             3.2.4 - Start Charging Session
System under test   Central System
Document Reference  Table 126, pages 112-113/176

Description         This scenario is used to stop the transaction when the cable is disconnected
                    at EV side.

Purpose             To test if the Central System can handle when the Charge Point stops the
                    transaction when the cable is disconnected at EV side, and it is configured
                    to do so.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      Charging
        (TODO: verify exact definition of reusable state "Charging" - assumed to be an
         active charging session reached via TC_003 or TC_004_1)

Test Scenario
1. [EV driver disconnects cable on EV side.]
   The Charge Point sends a StatusNotification.req to the Central System.
2. The Central System responds with a StatusNotification.conf.
3. The Charge Point sends a StopTransaction.req to the Central System.
4. The Central System responds with a StopTransaction.conf.
5. The Charge Point sends a StatusNotification.req to the Central System.
6. The Central System responds with a StatusNotification.conf.
7. [EV driver unplugs the cable from the Charge Point.]
   The Charge Point sends a StatusNotification.req to the Central System.
8. The Central System responds with a StatusNotification.conf.

Tool Validations
    Step 1 (Charge Point -> Central System):
        Message: StatusNotification.req
        - status is SuspendedEV
    Step 3 (Charge Point -> Central System):
        Message: StopTransaction.req
        - reason is EVDisconnected
    Step 5 (Charge Point -> Central System):
        Message: StatusNotification.req
        - status is Finishing
    Step 7 (Charge Point -> Central System):
        Message: StatusNotification.req
        - status is Available

Expected Result(s)  n/a (per official document)
"""
