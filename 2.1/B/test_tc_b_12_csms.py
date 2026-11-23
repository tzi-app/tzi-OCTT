"""
Test case name      Get Base Report - ConfigurationInventory
Test case Id        TC_B_12_CSMS
Use case Id(s)      B07
Requirement(s)      B07.FR.07

Requirement Details:
    B07.FR.07: Then the Charging Station SHALL respond with a NotifyReportRequest to report on all
               component-variables that can be set by the operator including their VariableCharacteristics.
        Precondition: B07.FR.01 AND When reportBase is ConfigurationInventory
System under test   CSMS

Description         CSMS requests a ConfigurationInventory base report.

Purpose             To test that CSMS supports the ConfigurationInventory base report.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. (CSMS) Manually instruct CSMS to retrieve a ConfigurationInventory report.
2. (Charging Station) Test System responds with:
    GetBaseReportResponse

Tool validations
* Step 1:
    Message: GetBaseReportRequest with:
    - requestId has integer value >= 0
    - reportBase = ConfigurationInventory

Post scenario validations:
    CSMS receives all NotifyReportRequest message for this requestId and is able to show the result of
    configuration inventory to an operator.
"""
