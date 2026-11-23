"""
Test case name      Clear Monitoring - Too many elements
Test case Id        TC_N_18_CSMS
Use case Id(s)      N06
Requirement(s)      N06.FR.04

Requirement Details:
    N06.FR.04: The CSMS SHALL NOT put more id elements in a ClearVariableMonitoringRequest than reported by
               the Charging Station via: ItemsPerMessageClearVariableMonitoring and
               BytesPerMessageClearVariableMonitoring.
System under test   CSMS

Description         CSMS is requested to clear more monitors than allowed in one request.

Purpose             To test that CSMS does not exceed the ItemsPerMessageClearVariableMonitoring amount of
                    monitors in one request.

Prerequisite(s)     CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.

Configuration State This test requests the value of ItemsPerMessageClearVariableMonitoring and then instructs
                    the CSMS to clear (at least) one more monitor than allowed by this value. This value is
                    'read-only', so it cannot be manipulated in the test. As a consequence, if the Charging
                    Station supports more monitor ids in the list, than can be set by the CSMS, then this
                    cannot be tested.

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Instruct CSMS to send GetVariablesRequest with:
    - Component.name MonitoringCtrlr
    - Variable.name ItemsPerMessage
    - Variable.instance ClearVariableMonitoring.
2. The Test System responds with:
    GetVariablesResponse
3. Instruct CSMS to clear more monitors than allowed in ItemsPerMessage.
    ClearVariableMonitoringRequest with a list of ids
    Note: these monitor ids do not have to exist.
4. The Test System responds with:
    ClearVariableMonitoringResponse

Tool validations
* Step 1:
    Message: Two or more ClearVariableMonitoringRequest, so that the maximum number of
             ItemsPerMessageClearVariableMonitoring ids is never exceeded.
    Test System will reply with a ClearVariableMonitoringResponse for each ClearVariableMonitoringRequest, but
    the content of the responses is irrelevant for the test.

Post scenario validations:
    N/A
"""
