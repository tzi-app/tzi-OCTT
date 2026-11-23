"""
Test case name      EMS Control - Set / Update External Charging Limit (not on a transaction) -
                    ChargingStationExternalConstraints in report
Test case Id        TC_K_52_CSMS
Use case Id(s)      K12
Requirement(s)      N/a
System under test   CSMS

Description         A charging schedule or charging limit can be removed by an external system on the Charging
                    Station. An external control system sends a signal to release a previously imposed
                    charging limit to a Charging Station. The Charging Station notifies the CSMS about this.

Purpose             To verify if the CSMS is able to correctly receive the report when a charging limit has
                    been externally changed in a charging station as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetChargingProfilesRequest
2. The Test System responds with a GetChargingProfilesResponse with
    - status Accepted
3. The Test System sends a ReportChargingProfilesRequest with
    - requestId Generated Id
    - chargingProfile.chargingProfilePurpose ChargingStationExternalConstraints
4. The CSMS responds with a ReportChargingProfilesResponse

Tool validations
N/a

Post scenario validations:
    - N/a
"""
