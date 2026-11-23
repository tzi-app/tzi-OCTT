"""
Test case name      Set Variable Monitoring - One SetMonitoringData element
Test case Id        TC_N_08_CSMS
Use case Id(s)      N04
Requirement(s)      N04.FR.01, N04.FR.02, N04.FR.17

Requirement Details:
    N04.FR.01: The Charging Station SHALL respond with an SetVariableMonitoringResponse with an equal (X)
               number of SetMonitoringResult elements, one for every SetMonitoringData element in the
               SetVariableMonitoringRequest.
        Precondition: When the Charging Station receives a SetVariableMonitoringRequest with an X number of
                      SetMonitoringData elements
    N04.FR.02: Every SetMonitoringResult element in the SetVariableMonitoringResponse SHALL contain the same
               component and variable combination as one of the SetVariableMonitoringRequest elements in the
               SetVariableMonitoringRequest.
        Precondition: N04.FR.01
    N04.FR.17: It is RECOMMENDED to use a value of 1.
        Precondition: When the CSMS sends a SetVariableMonitoringRequest with type Delta for a Variable that
                      is NOT of a numeric type
        Note: value is irrelevant for non-numeric types (e.g. any type except decimal or integer), since the
              monitor is triggered by every change of the Variable.
System under test   CSMS

Description         CSMS sends a request to activate monitoring on one variable.

Purpose             To test that CSMS supports setting monitoring on one variable.

Prerequisite(s)     CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.

Configuration State This test case activates monitoring on the following variable:
                    - Component "EVSE", evse <Configured evseId>, variable "AvailabilityState", monitor type
                      Delta
                    It assumes, that no monitor is active on this variable prior to the test.
                    Note 1: this is a required variable for which a monitor can be expected to exist or it can
                    be configured.
                    Note 2: Any other component/variable combination that supports monitoring could also be
                    used for this test case.

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. [CSMS] Request CSMS to install monitors on:
    - EVSE #<Configured evseId>, AvailabilityState, Delta, severity 8
2. [Charging Station] Test System responds with:
    Message: SetVariableMonitoringResponse with
    setMonitoringResult[0].status = Accepted

Tool validations
* Step 1:
    1. CSMS sends SetVariableMonitoringRequest with:
    - setMonitoringData[0].value = 1, ← recommended value for Delta monitor
    - setMonitoringData[0].type = Delta,
    - setMonitoringData[0].severity = 8,
    - setMonitoringData[0].component.name = "EVSE"
    - setMonitoringData[0].component.evse.id = <Configured evseId>
    - setMonitoringData[0].variable.name = "AvailabilityState"

Post scenario validations:
    N/A
"""
