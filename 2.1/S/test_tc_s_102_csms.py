"""
Test case name      Battery Swap - Remote Start - not enough batteries
Test case Id        TC_S_102_CSMS
Use case Id(s)      S01
Requirement(s)      N/a
System under test   CSMS

Description         CSMS is able to support battery swapping.

Purpose             To verify whether the CSMS is able successful support battery swapping with not enough
                    batteries.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Let CSMS trigger a request for swapping batteries

1. The CSMS sends a RequestBatterySwapRequest
2. The Test System responds with a RequestBatterySwapResponse with
    - status Rejected
    - statusInfo.reasonCode NoBatteryAvailable

Tool validations
* Step 1:
    Message: RequestBatterySwapRequest
    - requestId must be <not omitted>
    - idToken.idToken must be <Configured valid_idtoken_idtoken>

Post scenario validations:
    N/a
"""
