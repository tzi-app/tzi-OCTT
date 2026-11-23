"""
Test case name      Charging Station cancels reservation when Faulted
Test case Id        TC_H_20_CSMS
Use case Id(s)      H01
Requirement(s)      N/a
System under test   CSMS

Description         The Charging Station will cancel reservations, when the EVSE specified for a reservation
                    is set to an inoperative state.

Purpose             To verify if the CSMS is able to handle it when the reservation is canceled when the
                    availability state of the EVSE specified for the reservation is set to Faulted by the Test
                    System.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific EVSE.

1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse
    - With status Accepted
3. The Test System notifies the CSMS about the current state of the connector(s) of the configured EVSE
    Message: StatusNotificationRequest
    - with connectorStatus Reserved
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Reserved"
    - component.name "Connector"
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.
5. The Test System notifies the CSMS about the current state of the connector(s) of the configured EVSE
    Message: StatusNotificationRequest
    - with connectorStatus Faulted
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Faulted"
    - component.name "Connector"
    - variable.name "AvailabilityState"
6. The CSMS responds accordingly.
7. The Test System sends a ReservationStatusUpdateRequest
    - With reservationUpdateStatus Removed
    - reservationId <id received at step 1>
8. The CSMS responds with a ReservationStatusUpdateResponse

Tool validations
* Step 1:
    Message: ReserveNowRequest
    - evseId must be <Configured evseId>
    - connectorType must be omitted
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

Post scenario validations:
    N/a
"""
