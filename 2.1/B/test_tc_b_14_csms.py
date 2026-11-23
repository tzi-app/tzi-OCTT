"""
Test case name      Get Base Report - SummaryInventory
Test case Id        TC_B_14_CSMS
Use case Id(s)      B07
Requirement(s)      B07.FR.09

Requirement Details:
    B07.FR.09: Then the Charging Station SHALL respond with a NotifyReportRequest to report on components and
               variables related to the availability and condition of the Charging Station, notably
               operationalStatus of the Charging Station, EVSE and Connectors and any error condition.
        Precondition: B07.FR.01 AND When reportBase is SummaryInventory
        Note: A (summary) report that lists Components/Variables relating to the Charging Station’s current
              charging availability, and to any existing problem conditions. For the Charging Station
              Component:
              - AvailabilityState.
              For each EVSE Component:
              - AvailabilityState.
              For each Connector Component:
              - AvailabilityState (if known and different from EVSE).
              For all Components in an abnormal State:
              - Active (Problem, Tripped, Overload, Fallback) variables.
              - Any other diagnostically relevant Variables of the Components.
System under test   CSMS

Description         CSMS requests a SummaryInventory base report.

Purpose             To test that CSMS supports the SummaryInventory base report.

Prerequisite(s)     CSMS implementation supports the optional SummaryInventory report

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Manually instruct CSMS to retrieve a SummaryInventory report.
2. Test System responds with:
    GetBaseReportResponse

Tool validations
* Step 1:
    GetBaseReportRequest with:
    - requestId has integer value >= 0
    - reportBase = SummaryInventory

Post scenario validations:
    CSMS receives all NotifyReportRequest message for this requestId and is able to show the result of summary
    inventory to an operator.
"""
