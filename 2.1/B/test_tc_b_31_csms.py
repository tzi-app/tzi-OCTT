"""
Test case name      Cold Boot Charging Station - Pending/Rejected - TriggerMessage
Test case Id        TC_B_31_CSMS
Use case Id(s)      B02, F06
Requirement(s)      N/a
System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about
                    the Charging Station to the CSMS on startup AND it allows the Charging Station to request
                    whether it is allowed to start sending other OCPP messages.

Purpose             To verify whether the CSMS is able to send a TriggerMessageRequest to trigger a
                    BootNotificationRequest, before the interval expired.

Prerequisite(s)     The CSMS is configured to first respond to a BootNotificationRequest with status Pending
                    or Rejected.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a BootNotificationRequest
    - with reason PowerUp
    - chargingStation.model <Configured model>
    - chargingStation.vendorName <Configured vendorName>
2. The CSMS responds with a BootNotificationResponse
3. The CSMS sends a TriggerMessageRequest
4. The Test System responds with a TriggerMessageResponse
    - with status Accepted
5. The Test System sends a BootNotificationRequest
    - with reason Triggered
    - chargingStation.model <Configured model>
    - chargingStation.vendorName <Configured vendorName>
6. The CSMS responds with a BootNotificationResponse
7. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - with connectorStatus Available
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
8. The CSMS responds accordingly.

Tool validations
* Step 2:
    Message: BootNotificationResponse
    - status Pending OR Rejected
* Step 3:
    Message: TriggerMessageRequest
    - requestedMessage BootNotification
* Step 6:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a
"""
