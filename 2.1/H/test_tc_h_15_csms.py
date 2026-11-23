"""
Test case name      Reserve a connector with a specific type - Success
Test case Id        TC_H_15_CSMS
Use case Id(s)      H01(S3), H03
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve an EVSE with a connector with a specific type for a specific
                    IdToken by sending a ReserveNowRequest with a connectorType.

Purpose             To verify if the CSMS is able to request the Charging Station to reserve an EVSE with a
                    connector with a specific type, until the EV Driver with the specified IdToken arrives.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific ConnectorType.

1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse
    With status Accepted
3. The Test System notifies the CSMS about the current state of the connector
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
    - evseId must be omitted
    - connectorType must be <Configured connectorType>
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

Post scenario validations:
    N/a
"""
