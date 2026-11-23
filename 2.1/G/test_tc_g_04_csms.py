"""
Test case name      Change Availability EVSE - Inoperative to operative
Test case Id        TC_G_04_CSMS
Use case Id(s)      G03
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers how the CSMS requests the Charging Station to change the
                    availability of one of the EVSEs from Inoperative to Operative. An EVSE is considered
                    Operative in any status other than Faulted and Unavailable.

Purpose             To verify if the CSMS is able to perform the change availability mechanism as described at
                    the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        Unavailable for <Configured evseId>

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to change the availability of an EVSE to Operative.

1. The CSMS sends a ChangeAvailabilityRequest
2. The Test System responds with a ChangeAvailabilityResponse with status Accepted
3. The Test System notifies the CSMS about the current state of all connectors belonging to the specified EVSE
   (and optionally also from the EVSE itself).
    Message: StatusNotificationRequest
    - connectorStatus Available
    - evseId <Configured evseId>
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "EVSE" / Connector
    - component.evse.id <Configured evseId>
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message ChangeAvailabilityRequest
    - operationalStatus Operative
    - evse.id <Configured evseId>
    - connectorId omit

Post scenario validations:
    - N/a
"""
