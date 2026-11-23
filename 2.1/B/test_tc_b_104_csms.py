"""
Test case name      Reset ImmediateAndResume - Without ongoing transaction
Test case Id        TC_B_104_CSMS
Use case Id(s)      B13
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers how the CSMS can request the Charging Station to reset itself by
                    sending a ResetRequest without any ongoing transaction. This could for example be
                    necessary if the Charging Station is not functioning correctly.

Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP
                    specification.

Prerequisite(s)     CSMS has support for resuming transactions

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to reboot the Charging Station with type ImmediateAndResume

1. The CSMS sends a ResetRequest
2. The Test System responds with a ResetResponse
    with status Accepted
3. The Test System sends a BootNotificationRequest
4. The CSMS responds with a BootNotificationResponse
5. The Test System notifies the CSMS about the current state of all connectors.
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
6. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message ResetRequest
    - type ImmediateAndResume
* Step 4:
    Message BootNotificationResponse
    - status Accepted

Post scenario validations:
    - N/a
"""
