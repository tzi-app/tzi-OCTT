"""
Test case name      Set Monitoring Level - Out of range
Test case Id        TC_N_17_CSMS
Use case Id(s)      N05
Requirement(s)      N05.FR.02

Requirement Details:
    N05.FR.02: The Charging Station SHALL send a setMonitoringLevelResponse with Rejected .
        Precondition: When the Charging Station receives a setMonitoringLevelRequest for a severity that is
                      out of range
System under test   CSMS

Description         CSMS sets a monitoring level.

Purpose             To test that CSMS supports the rejection of setting of a monitoring level.

Prerequisite(s)     The Test System will always reject the message, but normally this would only occur if the
                    set severity level is out of range.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Instruct CSMS to set a monitoring level with severity = 4
2. Test System responds with:
    SetMonitoringLevelResponse with
    - Status is Rejected

Tool validations
* Step 1:
    Message: SetMonitoringLevelRequest with:
    - severity = 4

Post scenario validations:
    N/A
"""
