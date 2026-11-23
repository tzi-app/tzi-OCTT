"""
Test case name      Reserve a specific EVSE - Configured to Reject
Test case Id        TC_H_22_CSMS
Use case Id(s)      H01
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve a specific EVSE for a specific IdToken by sending a
                    ReserveNowRequest containing an evseId.

Purpose             To verify if the CSMS is able to correctly read the respond from a charging station when
                    it is configured not to accept reservations.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse with
    - status Rejected

Tool validations
N/a

Post scenario validations:
    N/a
"""
