"""
Test case name      Reserve a specific EVSE - Use a reserved EVSE with GroupId
Test case Id        TC_H_19_CSMS
Use case Id(s)      H01, H03
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve an EVSE for a specific group by sending a ReserveNowRequest
                    containing a groupIdToken.

Purpose             To verify if the CSMS is able to request the Charging Station create a reservation for a
                    specific group, by sending a ReserveNowRequest with a groupIdToken

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest with a groupIdToken for a specific EVSE.

1. The CSMS sends a ReserveNowRequest
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

Tool validations
* Step 1:
    Message: ReserveNowRequest
    - evseId must be <Configured evseId>
    - connectorType must be omitted
    - groupIdToken must be provided
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

Post scenario validations:
    N/a
"""
