"""
Test case name      Reservation of a Connector - Occupied
Test case Id        TC_048_2_CSMS
OCPP Version        1.6J
Section             3.17.1 - Reservation of a Connector
                    NOTE: OCTT document uses section 2.21.1 (to be verified)
Document Reference  Table 169, pages 144-145 of CompliancyTestTool-TestCaseDocument (2025-11)

Description         The Central System attempts to reserve a Connector, but the reservation
                    is not made, instead the status Occupied is returned by the Charge Point.

Purpose             Check whether the Central System can handle messages in case that a
                    reservation cannot be made.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
   [EV driver plugs in cable]
1. The Charge Point sends a StatusNotification.req to the Central System.
   - status: Preparing
   - connectorId: <Configured ConnectorId>
2. The Central System responds with a StatusNotification.conf to the Charge Point.
3. The Central System sends a ReserveNow.req to the Charge Point.
   - connectorId: same connectorId as in step 1
   - idTag: <Configured Valid IdTag>
   - reservationId: a unique reservation identifier chosen by the Central System
     NOTE: not explicitly listed in OCTT tool validations, inferred from OCPP spec (to be verified)
   - expiryDate: a future timestamp
     NOTE: not explicitly listed in OCTT tool validations, inferred from OCPP spec (to be verified)
4. The Charge Point responds with a ReserveNow.conf to the Central System.

Tool validations (Charge Point side):
* Step 1:
    Message: StatusNotification.req
    - status is "Preparing"
    - connectorId is <Configured ConnectorId>
* Step 4:
    Message: ReserveNow.conf
    - status is "Occupied"

Tool validations (Central System side):
* Step 3:
    Message: ReserveNow.req
    - connectorId should be the connectorId from step 1
    - idTag should be <Configured Valid IdTag>

Expected result(s):
    CP: n/a
    CS: The Central System accepts the Reservation message with the not Accepted status.
"""
