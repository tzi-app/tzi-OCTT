"""
Test case name      Trigger message - StatusNotification - Specific EVSE - Occupied
Test case Id        TC_F_24_CSMS
Use case Id(s)      F06
Requirement(s)      F06.FR.01, F06.FR.02, F06.FR.13

Requirement Details:
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
    F06.FR.02: The CSMS MAY indicate to which EVSE this request applies.
        Precondition: F06.FR.01. For every such requested message.
    F06.FR.13: The CSMS SHALL set the connectorId field
        Precondition: When sending a TriggerMessageRequest with requestedMessage set to: StatusNotification
        Note: StatusNotification messages can only be sent at connector level.
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to trigger the Charging Station to send a
                    StatusNotificationRequest for a specific occupied EVSE, using a TriggerMessageRequest.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System notifies the CSMS about the current state of the connector.
    Message: StatusNotificationRequest
    - connectorStatus Occupied
    - evseId <Configured evseId>
    - connectorId <Configured connectorId>
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Occupied"
    - component.name "Connector"
    - component.evse.id <Configured evseId>
    - component.evse.connectorid <Configured connectorId>
    - variable.name "AvailabilityState"
2. The CSMS responds accordingly.
3. The CSMS sends a TriggerMessageRequest
4. The Test System responds with a TriggerMessageResponse with status Accepted
5. The Test System notifies the CSMS about the current state of the connector.
    Message: StatusNotificationRequest
    - connectorStatus Occupied
    - evseId <Configured evseId>
    - connectorId <Configured connectorId>
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Occupied"
    - component.name "Connector"
    - component.evse.id <Configured evseId>
    - component.evse.connectorid <Configured connectorId>
    - variable.name "AvailabilityState"
6. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage must be StatusNotification
    - evse.id must be <Configured evseId>

Post scenario validations:
    N/a
"""
