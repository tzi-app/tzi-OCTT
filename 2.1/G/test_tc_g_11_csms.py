"""
Test case name      Change Availability EVSE - With ongoing transaction
Test case Id        TC_G_11_CSMS
Use case Id(s)      G03
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers how the CSMS requests the Charging Station to change the
                    availability of one of the EVSEs from Operative to Inoperative. An EVSE is considered
                    Operative in any status other than Faulted and Unavailable.

Purpose             To verify if the CSMS is able to send a change availability request during a transaction
                    according to the mechanism as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      State is EnergyTransferStarted

Test Scenario
Note(s): Request the CSMS to change the availablitiy to inoperative

1. The CSMS sends a ChangeAvailabilityRequest
2. The Test System responds with a ChangeAvailabilityResponse with
    status Scheduled

Note(s): Wait for <Configured Transaction Duration>

3. Execute Reusable State StopAuthorized
4. Execute Reusable State EVConnectedPostSession
5. Execute Reusable State EVDisconnected
6. The Test System notifies the CSMS about the current state of all connectors with
    Message: StatusNotificationRequest
    - connectorStatus Unavailable
    - evseId <Configured evseId>
    OR
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Unavailable"
    - component.name "Connector"
    - component.evse.id <Configured evseId>
    - variable.name "AvailabilityState"
7. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message ChangeAvailabilityRequest
    - operationalStatus Inoperative
    - evse.id <Configured evseId>
    - connectorId omit

Post scenario validations:
    - A respond to report the state of a connector has been received for all connectors.
"""
