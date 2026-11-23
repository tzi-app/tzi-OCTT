"""
Test case name      Reserve a specific EVSE - Accepted - Valid idToken
Test case Id        TC_H_01_CSMS
Use case Id(s)      H01(S2), H03
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve a specific EVSE for a specific IdToken by sending a
                    ReserveNowRequest containing an evseId.

Purpose             To verify if the CSMS is able to request the Charging Station to reserve a specific EVSE,
                    until the EV Driver with the specified IdToken arrives.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State Reserved for <Configured evseId>

Tool validations
N/a

Post scenario validations:
    N/a
"""
