"""
Test case name      Central V2X control with dynamic CSMS setpoint - push
Test case Id        TC_Q_109_CSMS
Use case Id(s)      Q04, K28
Requirement(s)      K28.FR.01, K28.FR.02

Requirement Details:
    K28.FR.01: A ChargingProfileType with chargingProfileKind = Dynamic SHALL consist of only 1
               ChargingScheduleType with only 1 ChargingSchedulePeriodType
    K28.FR.02: The ChargingSchedulePeriodType in a ChargingProfileType with chargingProfileKind = Dynamic
               SHALL have a startPeriod = 0
        Note: It becomes immediately active upon receipt of the message.
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to specify the power or current drawn by
                    EV.

Purpose             To verify if the CSMS is able to support DynamicControl charging profiles and push changes
                    to the CS.

Prerequisite(s)     - CSMS supports Bidirectional Power Transfer

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to send a TxDefaultProfile dynamic charging profile to the CS which will be
               periodically updated every <Configured dynamic profile update interval> seconds by CSMS with
               limit 6 * <limit multiplier>
Note: Check [csms_csKSmartChargingChargingProfileLimits] for <limit multiplier>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
3. The CSMS sends a UpdateDynamicScheduleRequest
4. The Test System responds with a UpdateDynamicScheduleResponse with
    - status Accepted
5. The CSMS sends a UpdateDynamicScheduleRequest
6. The Test System responds with a UpdateDynamicScheduleResponse with
    - status Accepted

Manual Action: Trigger the CSMS to clear the chargingProfile from step 1.

7. The CSMS sends a ClearChargingProfileRequest
8. The Test System responds with a ClearChargingProfileResponse with
    - status Accepted

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfileKind must be Dynamic
    - chargingProfile. must be TxDefaultProfile
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriods must be size 1
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].startPeriod must be 0
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].limit must be 6 * <limit multiplier>
    Note: Check [csms_csKSmartChargingChargingProfileLimits] for <limit multiplier>
* Step 3:
    Message: UpdateDynamicScheduleRequest
    - chargingProfileId must be <SetChargingProfileRequest.chargingProfile.id from step 1>
    - scheduleUpdate.limit must be <not omitted>
* Step 5:
    Message: UpdateDynamicScheduleRequest
    - chargingProfileId must be <SetChargingProfileRequest.chargingProfile.id from step 1>
    - scheduleUpdate.limit must be <not omitted>
* Step 7:
    Message: ClearChargingProfileRequest
    - chargingProfileId <chargingProfileId from step 1 chargingProfile>
    - chargingProfileCriteria omit

Post scenario validations:
    N/a
"""
