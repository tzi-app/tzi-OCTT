"""
Test case name      Get Base Report - FullInventory
Test case Id        TC_B_13_CSMS
Use case Id(s)      B07
Requirement(s)      B07.FR.08

Requirement Details:
    B07.FR.08: Then the Charging Station SHALL respond with a NotifyReportRequest to report on all
               component-variables including their VariableCharacteristics.
        Precondition: B07.FR.01 AND When reportBase is FullInventory
        Note: As a minimum the required variables mentioned in Charging Infrastructure related shall be
              reported as well as the required variables in Section 1 Controller Components that are relevant
              to each functional block that has been implemented.
System under test   CSMS

Description         CSMS requests a FullInventory base report.

Purpose             To test that CSMS supports the FullInventory base report.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Manually instruct CSMS to retrieve a FullInventory report.
2. Test System responds with:
    GetBaseReportResponse

Tool validations
* Step 1:
    GetBaseReportRequest with:
    - requestId has integer value >= 0
    - reportBase = FullInventory

Post scenario validations:
    CSMS receives all NotifyReportRequest message for this requestId and is able to show the result of full
    inventory to an operator.
"""
