"""
Test case name      Reservation of a Connector - Faulted
Test case Id        TC_048_1_CSMS
OCPP Version        1.6J
Section             3.17.1 - Reservation of a Connector
Document ref        CompliancyTestTool-TestCaseDocument, Table 168, Page 144/176

Description         The Central System attempts to reserve a Connector, but the reservation
                    is not made, instead the status Faulted is returned by the Charge Point.

Purpose             Check whether the Central System is able to handle messages in case
                    that a reservation cannot be made.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Scenario Detail(s)
    Charge Point (Tool):
        2. The Charge Point responds with a ReserveNow.conf
    Central System (SUT):
        1. The Central System sends a ReserveNow.req
           - connectorId: <Configured ConnectorId>
           - idTag: <Configured Valid IdTag>
           - reservationId: a unique reservation identifier chosen by the Central System
           - expiryDate: a future timestamp

Tool validations (Charge Point side):
* Step 2:
    Message: ReserveNow.conf
    - status is "Faulted"

Tool validations (Central System side):
* Step 1:
    Message: ReserveNow.req
    - connectorId should be <Configured ConnectorId>
    - idTag should be <Configured Valid IdTag>

Expected result(s) / behaviour:
    Charge Point (Tool): n/a
    Central System (SUT): The Central System accepts the Reservation message
                          with the not Accepted status.
"""
