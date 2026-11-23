"""
Test case name      Get Monitoring report - Report all
Test case Id        TC_N_47_CSMS
Use case Id(s)      N02
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how the CSMS requests the Charging Station to send a report about
                    configured monitoring settings per component and variable. Optionally, this list can be
                    filtered on monitoringCriteria and componentVariables.

Purpose             To verify if the CSMS is able to send a get monitor request omitting the
                    monitoringCriteria and componentVariable as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetMonitoringReportRequest
2. The Test System responds with a GetMonitoringReportResponse
3. The Test System sends a NotifyMonitoringReportRequest
4. The CSMS responds with a NotifyMonitoringReportResponse.

Note(s):
- If tbc is True at Step 3 then step 3 and 4 will be repeated

Tool validations
* Step 1:
    Message GetMonitoringReportRequest
    - monitoringCriteria omitted AND
    - componentVariable omitted.

Post scenario validations:
    - N/a
"""
