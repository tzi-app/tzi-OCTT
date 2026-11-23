"""
Test case name      Frequency Support - Central V2X control - push
Test case Id        TC_Q_117_CSMS
Use case Id(s)      Q07, Q04, K28
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
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to support DynamicControl charging profiles and push changes
                    to the CS.

Prerequisite(s)     - CSMS supports Bidirectional Power Transfer

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to send a TxDefaultProfile dynamic charging profile to the CS and update the
               schedule every 15 seconds with
    - operationMode CentralFrequency
    - setpoint -6 * <limit multiplier>
    Note: Check [csms_csKSmartChargingChargingProfileLimits] for <limit multiplier>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with status Accepted
3. The CSMS sends a UpdateDynamicScheduleRequest
4. The Test System responds with a UpdateDynamicScheduleResponse with status Accepted

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfileKind must be Dynamic
    - chargingProfile. must be TxDefaultProfile
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriods must be size 1
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].startPeriod must be 0
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpoint must be -6 * <limit multiplier>
    Note: Check [csms_csKSmartChargingChargingProfileLimits] for <limit multiplier>
* Step 3:
    Message: UpdateDynamicScheduleRequest
    - chargingProfileId must be <SetChargingProfileRequest.chargingProfile.id from step 1>
    - scheduleUpdate.limit must be <not omitted>

Post scenario validations:
    N/a
"""
