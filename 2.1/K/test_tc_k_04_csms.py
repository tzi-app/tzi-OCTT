"""
Test case name      Replace charging profile - With chargingProfileId
Test case Id        TC_K_04_CSMS
Use case Id(s)      n/a
Requirement(s)      n/a
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to replace a charging profile with the same ProfileKind,
                    Purpose, and stackLevel, but a different limit.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a SetChargingProfileRequest with
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 8.0 or 8000.0
2. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
3. The CSMS sends a SetChargingProfileRequest with
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 6.0 or 6000.0
4. The Test System responds with a SetChargingProfileResponse with
    - status Accepted

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 8.0 (A) or 8000.0 (W)
    The chargingSchedule contains only one chargingSchedulePeriod
* Step 3:
    Message SetChargingProfileRequest
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 6.0 (A) or 6000.0 (W)
    The chargingSchedule contains only one chargingSchedulePeriod
* Step 1/3:
    Message SetChargingProfileRequest
    - chargingProfile.id <Same id for both chargingProfiles>
    - chargingProfile.chargingSchedule.startSchedule must NOT be omitted.
    - chargingProfile.stackLevel <Configured stackLevel> AND
    - chargingProfile.chargingProfilePurpose <Equal value for both profiles> AND (TxDefaultProfile OR
      ChargingStationMaxProfile)
    - chargingProfile.chargingProfileKind <Equal value for both profiles> AND
    If chargingProfile.chargingProfilePurpose is TxDefaultProfile then chargingProfile.chargingProfileKind
    must be Absolute OR Recurring
    If chargingProfile.chargingProfilePurpose is ChargingStationMaxProfile then
    chargingProfile.chargingProfileKind must be Absolute
    If chargingProfile.chargingProfileKind is Recurring then chargingProfile.recurrencyKind must NOT be
    omitted, else omitted

    The received Charging Profiles must comply with the requirements defined at part 2 specification.

Post scenario validations:
    - N/a
"""
