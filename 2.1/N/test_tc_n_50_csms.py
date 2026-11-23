"""
Test case name      Alert Event - Periodic Triggered
Test case Id        TC_N_50_CSMS
Use case Id(s)      N07
Requirement(s)      N/a
System under test   CSMS

Description         NotifyEventRequest reports every Component/Variable for which a VariableMonitoring setting
                    was triggered. Only the VariableMonitoring settings that are responsible for triggering an
                    event are included.

Purpose             To verify if the CSMS is able to read a request when a trigger reason is periodic after a
                    reboot as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The Test System sends a NotifyEventRequest with
    - eventData.trigger Periodic
2. The CSMS responds with a NotifyEventResponse.

Tool validations
N/a

Post scenario validations:
    - N/a
"""
