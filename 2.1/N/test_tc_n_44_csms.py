"""
Test case name      Clear Monitoring - Rejected
Test case Id        TC_N_44_CSMS
Use case Id(s)      N06
Requirement(s)      N/a
System under test   CSMS

Description         A monitoring setting can be cleared (removed) by sending a ClearVariableMonitoringRequest
                    with the id of the monitoring setting.

Purpose             To verify if the CSMS is able to correctly read the respond from a charging station on a
                    request to clear a monitor that cannot be cleared as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a ClearVariableMonitoringRequest
2. The Test System responds with a ClearVariableMonitoringResponse with clearMonitoringResult[0].status
   Rejected

Tool validations
N/a

Post scenario validations:
    - N/a
"""
