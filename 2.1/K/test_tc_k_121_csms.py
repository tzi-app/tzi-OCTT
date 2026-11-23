"""
Test case name      Dynamic charging profiles from CSMS - Pull
Test case Id        TC_K_121_CSMS
Use case Id(s)      K28
Requirement(s)      K28.FR.01, K28.FR.02, K28.FR.07, K28.FR.12

Requirement Details:
    K28.FR.01: A ChargingProfileType with chargingProfileKind = Dynamic SHALL consist of only 1
               ChargingScheduleType with only 1 ChargingSchedulePeriodType
    K28.FR.02: The ChargingSchedulePeriodType in a ChargingProfileType with chargingProfileKind = Dynamic
               SHALL have a startPeriod = 0
        Note: It becomes immediately active upon receipt of the message.
    K28.FR.07: CSMS SHALL respond with PullDynamicScheduleUpdateResponse with status = Accepted and the
               limits/setpoints to use in the charging profile.
        Precondition: When CSMS receives a PullDynamicScheduleUpdateRequest for a charging profile that has
                      chargingProfileKind = Dynamic
    K28.FR.12: CSMS SHALL respond with a status = Rejected and optionally a statusInfo.reasonCode =
               InvalidProfile
        Precondition: When CSMS receives a PullDynamicScheduleUpdateRequest for a charging profile that does
                      not exist or does not have chargingProfileKind = Dynamic
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to support DynamicControl charging profiles.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to send a dynamic charging profile to the CS

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with status Accepted
3. The Test System sends a PullDynamicScheduleUpdateRequest with
    - chargingProfileId <unknown chargingProfileId>
4. The CSMS responds with a PullDynamicScheduleUpdateResponse
5. The Test System sends a PullDynamicScheduleUpdateRequest with
    - chargingProfileId must be <chargingProfileId received in step 1>
6. The CSMS responds with a PullDynamicScheduleUpdateResponse

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfileKind must be Dynamic
    - chargingProfile.chargingSchedule must be size = 1
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriods must be size = 1
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].startPeriod must be 0
* Step 4:
    Message: PullDynamicScheduleUpdateResponse
    - status must be Rejected
* Step 6:
    Message: PullDynamicScheduleUpdateResponse
    - status must be Accepted
    - scheduleUpdate must be <not omitted>
    - scheduleUpdate must at least have a single field set

Post scenario validations:
    N/a
"""
