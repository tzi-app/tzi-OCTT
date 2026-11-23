"""
Test case name      Charging station reporting a DER event
Test case Id        TC_R_108_CSMS
Use case Id(s)      R05
Requirement(s)      N/a
System under test   CSMS

Description         Configure a DER Control which will always trigger and halfs the charging rate of the
                    charging profile when a transaction starts, then add onother DER Control to test
                    overriding the previous one. After tha clearing all DER controls to test it reports the
                    alert should be cleared.

Purpose             To check if the CSMS supports receiving DER events.

Prerequisite(s)     CSMS supports DER Control

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Report DER alarm
1. The Test System sends a NotifyDERAlarmRequest with
    - controlType LVMustTrip
    - gridEventFault UnderVoltage
    - alarmEnded false
    - timestamp <Current DateTime>
2. The CSMS responds with a NotifyDERAlarmResponse

Note: The Test System waits 5 seconds

Clear DER alarm
3. The Test System sends a NotifyDERAlarmRequest with
    - controlType LVMustTrip
    - gridEventFault UnderVoltage
    - alarmEnded true
    - timestamp <Current DateTime>
4. The CSMS responds with a NotifyDERAlarmResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
