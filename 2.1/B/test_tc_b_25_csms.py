"""
Test case name      Reset EVSE - Without ongoing transaction
Test case Id        TC_B_25_CSMS
Use case Id(s)      B11
Requirement(s)      B11.FR.04

Requirement Details:
    B11.FR.04: The Charging Station SHALL proceed as described in use case B01 - Cold Boot Charging Station.
        Precondition: B11.FR.03
System under test   CSMS

Description         This test case covers how the CSMS can request the Charging Station to reset an EVSE by
                    sending a ResetRequest without any ongoing transaction. This could for example be
                    necessary if the Charging Station is not functioning correctly.

Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP
                    specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to reboot an EVSE with status OnIdle

1. The CSMS sends a ResetRequest with:
    - status OnIdle
    - evseID <Configured evseId>
2. The Test System responds with a ResetResponse with status Accepted

Tool validations
* Step 1:
    Message ResetRequest
    - type OnIdle
    - evseId <Configured evseId>

Post scenario validations:
    - N/a
"""
