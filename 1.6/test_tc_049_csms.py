"""
Test case name      Reservation of a Charge Point - Transaction
Test case Id        TC_049_CSMS
OCPP Version        1.6J
Section             3.17.2 - Reservation of a Charge Point
Document Reference  Table 172, page 146 (CompliancyTestTool-TestCaseDocument)

Description         A Charge Point / unspecified Connector is reserved and a charging
                    transaction takes place.

Purpose             Check whether Central System trigger the Charge Point to reserve
                    an unspecified Connector.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    Charge Point (Tool)                         Central System (SUT)
    ───────────────────                         ────────────────────
                                                1. The Central System sends a ReserveNow.req
                                                   with a reservationId, connectorId and idTag
                                                   to the Charge Point
    2. The Charge Point sends a
       ReserveNow.conf message to the
       Central System
    3. The Charge Point sends a
       StatusNotification.req to the
       Central System
                                                4. The Central System sends a
                                                   StatusNotification.conf to the Charge Point

Tool validations (Charge Point side):
* Step 3:
    Message: StatusNotification.req
    - The status is Reserved

Tool validations (Central System side):
* Step 1:
    Message: ReserveNow.req
    - The connectorId is 0

Expected result(s) / behaviour:
    Charge Point:
        The Charge Point handles the reservation correctly, only the idTag
        from the reservation can charge, on any available connector of the
        Charge Point.
    Central System:
        The Central System accepts the reservation for the right idTag and
        reservationId.

Notes (to be verified/fixed later):
    - The doc's Purpose text appears to have a grammar issue ("trigger" instead
      of "triggers" or "can trigger") — kept as-is from the document.
    - ReserveNow.req requires an expiryDate field per the OCPP 1.6 spec, but
      the document's scenario step 1 only explicitly mentions reservationId,
      connectorId, and idTag. The expiryDate should still be set to a future
      timestamp in the implementation.
"""
