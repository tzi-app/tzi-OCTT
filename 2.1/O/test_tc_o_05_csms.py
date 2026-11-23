"""
Test case name      Clear Display Message - Unknown Key
Test case Id        TC_O_05_CSMS
Use case Id(s)      O05
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can remove a specific message, configured via OCPP in a
                    Charging Station.

Purpose             To verify if the CSMS is able to request the Charging Station to clear a message according
                    to the mechanism as described in the OCPP specification.

Prerequisite(s)     If the CSMS supports sending a ClearDisplayMessageRequest with an unknown id.

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a ClearDisplayMessageRequest
2. The Test System responds with a ClearDisplayMessageResponse with status Unknown

Tool validations
N/a

Post scenario validations:
    - N/a
"""
