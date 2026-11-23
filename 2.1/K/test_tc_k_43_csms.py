"""
Test case name      Get Composite Schedule - Specific EVSE
Test case Id        TC_K_43_CSMS
Use case Id(s)      K08
Requirement(s)      K08.FR.01

Requirement Details:
    K08.FR.01: The CSMS MAY request the Charging Station to report the CompositeSchedule by sending
               GetCompositeScheduleRequest.
System under test   CSMS

Description         The CSMS requests a composite schedule which is a combination of local limits and the
                    prevailing Charging Profiles of the different chargingProfilePurposes and stack levels.

Purpose             To verify if the CSMS is able to calculate request a composite schedule from the Charging
                    Station for a specific EVSE.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a GetCompositeScheduleRequest
2. The Test System responds with a GetCompositeScheduleResponse
    - With status Accepted
    - schedule.evseId 1
    - schedule.duration is 300
    - schedule.chargingRateUnit <Specified chargingRateUnit from step 1>
    - schedule.chargingSchedulePeriod[0].startPeriod 0
    Note: Multiply limit by 1000 if chargingRateUnit is W
    - schedule.chargingSchedulePeriod[0].limit 10

Tool validations
* Step 1:
    Message GetCompositeScheduleRequest
    - evseId 1
    - duration is <Configured duration>
    - chargingRateUnit <Configured chargingRateUnit>

Post scenario validations:
    N/a
"""
