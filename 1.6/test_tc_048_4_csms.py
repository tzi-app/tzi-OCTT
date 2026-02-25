"""
Test case name      Reservation of a Connector - Rejected
Test case Id        TC_048_4_CSMS
OCPP Version        1.6J
Section             3.17.1 - Reservation of a Connector
Document ref        Table 171, page 146 (CompliancyTestTool-TestCaseDocument)

Description         The Central System attempts to reserve a Connector, but the reservation
                    is not made, instead the status Rejected is returned by the Charge Point.

Purpose             Check whether the Central System can handle messages in case that a
                    reservation cannot be made.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Pre-conditions
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System sends a ReserveNow.req to the Charge Point.
   - connectorId: <Configured ConnectorId>
   - idTag: <Configured Valid IdTag>
   - reservationId: a unique reservation identifier chosen by the Central System
   - expiryDate: a future timestamp
2. The Charge Point responds with a ReserveNow.conf to the Central System.

Tool validations (Charge Point side):
* Step 2:
    Message: ReserveNow.conf
    - status is "Rejected"

Tool validations (Central System side):
* Step 1:
    Message: ReserveNow.req
    - connectorId should be <Configured ConnectorId>
    - idTag should be <Configured Valid IdTag>

Expected result(s):
    The Central System accepts the Reservation message with the not Accepted status (Rejected).
    NOTE: "The Central System does not assume the connector is reserved" - this is implied
    behaviour but is NOT explicitly stated in the official test case document. To be verified.
"""
