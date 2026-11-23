"""
Test case name      Alert Event - Variable monitoring on write only
Test case Id        TC_N_48_CSMS
Use case Id(s)      N07
Requirement(s)      N/a
System under test   CSMS

Description         NotifyEventRequest reports every Component/Variable for which a VariableMonitoring setting
                    was triggered. Only the VariableMonitoring settings that are responsible for triggering an
                    event are included.

Purpose             To verify if the CSMS is able to read a request from a trigger from a variablemonitor
                    which is write only as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The Test System sends a NotifyEventRequest with
    - eventData.actualValue empty
2. The CSMS responds with a NotifyEventResponse.

Tool validations
N/a

Post scenario validations:
    - N/a
"""
