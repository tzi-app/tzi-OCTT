"""
Test case name      Get Custom Report - with componentCriteria and component/variables
Test case Id        TC_B_18_CSMS
Use case Id(s)      B08
Requirement(s)      B08.FR.01, B08.FR.03

Requirement Details:
    B08.FR.01: The Charging Station SHALL send a GetReportResponse with Accepted
        Precondition: NOT B08.FR.15 AND NOT B08.FR.16 AND When the Charging Station receives a
                      GetReportRequest for supported criteria
    B08.FR.03: The Charging Station SHALL send the requested information, excluding the value of WriteOnly
               variables, via one or more NotifyReportRequest messages to the CSMS.
        Precondition: B08.FR.01
System under test   CSMS

Description         CSMS requests a report of components that match both the component criteria
                    and the given list of components and variables.

Purpose             To test that CSMS supports requesting a report for both the component criteria and a given
                    list of components and optionally with variables and that it handles an empty result set.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Manually instruct CSMS to get the value of:
    - EVSE #1::AvailabiltyState
    - from all Problem components
2. Test System responds with:
    GetReportResponse with
    status EmptyResultSet
3. Manually instruct CSMS to get the value of:
    - EVSE #1::AvailabiltyState
    - from all Available components
4. Test System responds with:
    GetReportResponse with
    status Accepted
5. Test System responds with:
    NotifyReportRequest
6. CSMS sends NotifyReportResponse

Tool validations
* Step 1:
    Message: GetReportRequest
    - componentCriteria = Problem
    - componentVariable[0].component.name = "EVSE"
    - componentVariable[0].component.evse.id = 1
    - componentVariable[0].variable.name = "AvailabilityState"
* Step 3:
    Message: GetReportRequest
    - componentCriteria is Available
    - componentVariable[0].component.name = "EVSE"
    - componentVariable[0].component.evse.id = 1
    - componentVariable[0].variable.name = "AvailabilityState"

Post scenario validations:
    N/A
"""
