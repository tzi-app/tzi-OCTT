"""
Test case name      Reserve a specific EVSE - Reservation Ended / not used
Test case Id        TC_H_07_CSMS
Use case Id(s)      H01(S2), H04
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve a specific EVSE for a specific IdToken by sending a
                    ReserveNowRequest containing an evseId.

Purpose             To verify if the CSMS is able to handle a reservation that is canceled by the Charging
                    Station, because the EV driver did not arrive before the set expiryDateTime was reached.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific EVSE.

1. The CSMS sends a ReserveNowRequest with
    - expiryDateTime current time + <configured transaction duration>
2. The Test System responds with a ReserveNowResponse
    With status Accepted
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
    - with connectorStatus Available
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
    Note(s):
    - The Test System waits until the provided expiryDateTime from step 1 expires before executing this step.
6. The CSMS responds accordingly.
7. The Test System sends a ReservationStatusUpdateRequest
    With reservationUpdateStatus Expired
    reservationId <id received at step 1>
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
