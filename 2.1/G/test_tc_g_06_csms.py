"""
Test case name      Change Availability Charging Station - Inoperative to operative
Test case Id        TC_G_06_CSMS
Use case Id(s)      G04
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how the CSMS requests the Charging Station to change the
                    availability from inoperative to operative.

                    A Charging Station is considered Operative when it is charging or ready for charging.

                    A Charging Station is considered Inoperative when it does not allow any charging.

Purpose             To verify if the CSMS is able to perform the change availability mechanism as described at
                    the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   Charging Station set to Unavailable (Original status was Available)

Test Scenario
Manual Action: Request the CSMS to change the availability of the Charging Station to Inoperative.

1. The CSMS sends a ChangeAvailabilityRequest
2. The Test System responds with a ChangeAvailabilityResponse with status Accepted
3. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message ChangeAvailabilityRequest
    - operationalStatus Operative
    - evseId omit
    - connectorId omit

Post scenario validations:
    - N/a
"""
