"""
Test case name      Cancel reservation of an EVSE - Success
Test case Id        TC_H_17_CSMS
Use case Id(s)      H02
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to cancel a reservation by sending a CancelReservationRequest to the
                    Charging Station.

Purpose             To verify if the CSMS is able to request the Charging Station to cancel a reservation, by
                    sending a CancelReservationRequest

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific EVSE.

1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse
    with status Accepted
3. The Test System notifies the CSMS about the current state of the connector(s) of the configured EVSE
    Message: StatusNotificationRequest
    - with connectorStatus Reserved
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Reserved"
    - component.name "Connector"
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Manual Action: Trigger the CSMS to send a CancelReservationRequest for the reservation created at step 1.

5. The CSMS sends a CancelReservationRequest
6. The Test System responds with a CancelReservationResponse
    With status Accepted
7. The Test System notifies the CSMS about the current state of the connector(s) of the configured EVSE
    Message: StatusNotificationRequest
    - with connectorStatus Available
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
8. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: ReserveNowRequest
    - evseId must be <Configured evseId>
    - connectorType must be omitted
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
* Step 5:
    Message: CancelReservationRequest
    - reservationId must be equal to the id provided at step 1

Post scenario validations:
    N/a
"""
