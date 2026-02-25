"""
Test case name      Cancel Reservation - Rejected
Test case Id        TC_052_CSMS
OCPP Version        1.6J
Section             3.17.3 - Cancel Reservation
Document ref        OCPP Compliancy Testing Tool - TestCaseDocument (2025-11),
                    Table 174, page 148/176

Description         The Central System tries to cancel reservation, but this request
                    is rejected by the Charge Point.

Purpose             Check whether the Central System can handle messages in case cancelling
                    a reservation is rejected by the Charge Point.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
   [Manual Action: Reserve a connector on the Charge Point]
1. The Central System sends a ReserveNow.req to the Charge Point.
   - connectorId: <Configured ConnectorId>
   - idTag: <Configured Valid IdTag>
   - reservationId: a unique reservation identifier chosen by the Central System
   - expiryDate: a future timestamp
   NOTE: Parameters above are not explicitly listed in the CSMS test case document;
   they are standard OCPP 1.6 ReserveNow.req fields (to be verified later).
2. The Charge Point responds with a ReserveNow.conf to the Central System.
3. The Charge Point sends a StatusNotification.req to the Central System.
4. The Central System responds with a StatusNotification.conf to the Charge Point.

   [Manual Action: Cancel the reservation on the Charge Point]
   (The reservation is cancelled locally on the Charge Point so that the
    CancelReservation.req from the Central System will find no matching reservation.)

5. The Central System sends a CancelReservation.req to the Charge Point.
   - reservationId: a reservation identifier (which no longer exists on the Charge Point)
6. The Charge Point responds with a CancelReservation.conf to the Central System.

Tool validations (Charge Point side):
* Step 2:
    Message: ReserveNow.conf
    - status is "Accepted"
* Step 3:
    Message: StatusNotification.req
    - status is "Reserved"
* Step 6:
    Message: CancelReservation.conf
    - status is "Rejected"

Tool validations (Central System side):
    (No specific Central System validations defined in the document)

Expected result(s):
    The Charge Point rejects the reservationId and does not cancel any reservation.
    The Central System processes the rejection from the Charge Point to the
    cancel reservation message.
"""
