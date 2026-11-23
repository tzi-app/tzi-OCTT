"""
Test case name      Set Monitoring Level - Success
Test case Id        TC_N_16_CSMS
Use case Id(s)      N05
Requirement(s)      N05.FR.01

Requirement Details:
    N05.FR.01: The Charging Station SHALL send a setMonitoringLevelResponse with Accepted.
        Precondition: When the Charging Station accepts a setMonitoringLevelRequest
System under test   CSMS

Description         CSMS sets a monitoring level.

Purpose             To test that CSMS supports setting of a monitoring level.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Instruct CSMS to set a monitoring level with severity = _4
2. Test System responds with:
    SetMonitoringLevelResponse with
    - Status is Accepted

Tool validations
* Step 1:
    Message: SetMonitoringLevelRequest with:
    - severity = 4

Post scenario validations:
    N/A
"""
