"""
Test case name      Reserve an unspecified EVSE - Accepted
Test case Id        TC_H_08_CSMS
Use case Id(s)      H01(S1), H03
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve an unspecified EVSE for a specific IdToken by sending a
                    ReserveNowRequest without an evseId.

Purpose             To verify if the CSMS is able to request the Charging Station to reserve an unspecified
                    EVSE, until the EV Driver with the specified IdToken arrives.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest for an unspecified EVSE.

1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse with status Accepted
3. The Test System notifies the CSMS about the current state of the connector(s) of the configured EVSE
    Message: StatusNotificationRequest
    - with connectorStatus Reserved
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Reserved"
    - component.name "Connector"
    - variable.name "AvailabilityState"
    Note(s):
    - The Test System will execute this step, if it is configured with only one EVSE.
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
