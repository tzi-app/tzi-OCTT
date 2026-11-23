"""
Test case name      Reserve an unspecified EVSE - Amount of EVSEs available equals the amount of reservations
Test case Id        TC_H_14_CSMS
Use case Id(s)      H01(S1)
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve an unspecified EVSE for a specific IdToken by sending a
                    ReserveNowRequest without an evseId.

Purpose             To verify if the CSMS is able to handle that the Charging Station sets all available EVSE
                    to reserved, when the amount of EVSEs available equals the amount of reservations.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest for an unspecified EVSE.

1. The CSMS sends a ReserveNowRequest
    Note(s):
    - This step needs to executed time the amount of EVSE configured for the Test System.
2. The Test System responds with a ReserveNowResponse with status Accepted
3. The Test System notifies the CSMS about the current state of all connectors
    Message: StatusNotificationRequest
    - with connectorStatus Reserved
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Reserved"
    - component.name "Connector"
    - variable.name "AvailabilityState"
    Note(s):
    - This step will be executed after the last ReserveNowRequest has been sent from step 1.
4. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: ReserveNowRequest
    - evseId must be omitted
    - connectorType must be omitted
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

Post scenario validations:
    N/a
"""
