"""
Test case name      EMS Control - Set / Update External Charging Limit (not on a transaction)
Test case Id        TC_K_48_CSMS
Use case Id(s)      K12
Requirement(s)      N/a
System under test   CSMS

Description         A charging schedule or charging limit can be imposed by an external system on the Charging
                    Station for new transactions or on the grid connection. An External Control System sends a
                    charging limit to a Charging Station. This limit is then sent to the CSMS.

Purpose             To verify if the CSMS is able to receive the request from a charging station and respond
                    correctly as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The Test System sends a NotifyChargingLimitRequest with
    - chargingLimit.chargingLimitSource EMS
2. The CSMS responds with a NotifyChargingLimitResponse

Tool validations
- N/a

Post scenario validations:
    - N/a
"""
