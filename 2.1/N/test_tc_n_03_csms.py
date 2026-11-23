"""
Test case name      Get Monitoring Report - with component criteria and component/variable
Test case Id        TC_N_03_CSMS
Use case Id(s)      N02
Requirement(s)      N02.FR.05, N02.FR.10

Requirement Details:
    N02.FR.05: The set of monitors reported in one or more notifyMonitoringReportRequest messages is limited
               to the set defined by monitoringCriteria and componentVariables.
        Precondition: N02.FR.01 AND monitoringCriteria and componentVariables are NOT both absent.
    N02.FR.10: The Charging Station SHALL respond with a GetMonitoringReportResponse(status=EmptyResultSet).
        Precondition: When the Charging Station receives a GetMonitoringReportRequest with a combination of
                      criteria which results in an empty result set.
System under test   CSMS

Description         CSMS requests a report of monitors that match both the component criteria
                    and the given list of components and variables.

Purpose             To test that CSMS supports requesting a monitoring report for both the component criteria
                    and a given component and variable and that it handles an empty result set.

Prerequisite(s)     CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.

Configuration State N/a

Memory State        CSMS requests ClearVariableMonitoring ItemsPerMessage from CS.

Reusable State(s)   N/a

Test Scenario
Manual Action: Manually instruct CSMS to get a report of monitors for:
    - all DeltaMonitoring
    - and the variable AvailabilityState for EVSE #1.

1. CSMS sends GetMonitoringReportRequest
2. Test System responds with:
    GetMonitoringReportResponse with:
    - Status EmptyResultSet

Manual Action: Manually instruct CSMS to get a report of monitors for:
    - all ThresholdMonitoring
    - and the variable Power of ChargingStation.

3. CSMS sends GetMonitoringReportRequest
4. Test System responds with:
    GetMonitoringReportResponse with:
    - Status Accepted
5. Test System responds with:
    NotifyMonitoringReportRequest
6. CSMS sends NotifyMonitoringReportResponse

Step 5 and 6 are repeated as often as needed to report all configuration variables.

Tool validations
* Step 1:
    Message: GetMonitoringReportRequest
    - monitoringCriteria = DeltaMonitoring
    - componentVariable[0].component.name = "EVSE"
    - componentVariable[0].component.evse.id = <configured evseId>
    - componentVariable[0].variable.name = "AvailabilityState"
* Step 3:
    Message: GetMonitoringReportRequest
    - monitoringCriteria = ThresholdMonitoring
    - componentVariable[0].component.name = "ChargingStation"
    - componentVariable[0].variable.name = "Power"

Post scenario validations:
    Check that CSMS shows the Threshold monitors for Power for ChargingStation.
"""
