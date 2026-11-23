"""
Test case name      Get Monitoring report - TargetDeltaMonitoring
Test case Id        TC_N_104_CSMS
Use case Id(s)      N02
Requirement(s)      …
System under test   CSMS

Description         CSMS requests a report of monitors that match the component criteria.

Purpose             To test that CSMS supports requesting a monitoring report for the component criteria and
                    that it handles an empty result set.

Prerequisite(s)     CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger CSMS to get a report of monitors for DeltaMonitoring

1. CSMS sends GetMonitoringReportRequest
2. Test System responds with a GetMonitoringReportResponse with
    - Status Accepted
3. Test System responds with a NotifyMonitoringReportRequest with
    - requestId <GetMonitoringReportRequest.requestId from step 1>
    - tbc false
    - seqNo 0
    - monitor[0].component.name EVSE
    - monitor[0].component.evse.id 1
    - monitor[0].variable.name Power
    - monitor[0].variableMonitoring[0].type TargetDeltaRelative
    - monitor[0].variableMonitoring[0].transaction = false
    - monitor[0].variableMonitoring[0].value = 5
    - monitor[0].variableMonitoring[0].eventNotificationType = <not omitted>
    - monitor[0].variableMonitoring[1].type TargetDelta
    - monitor[0].variableMonitoring[1].transaction = false
    - monitor[0].variableMonitoring[1].value = 5
    - monitor[0].variableMonitoring[1].eventNotificationType = <not omitted>
4. CSMS sends NotifyMonitoringReportResponse

Tool validations
* Step 1:
    Message: GetMonitoringReportRequest
    - monitoringCriteria = DeltaMonitoring

Post scenario validations:
    N/a
"""
