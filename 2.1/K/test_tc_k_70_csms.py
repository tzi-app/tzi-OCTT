"""
Test case name      Set Charging Profile - Multiple Profiles
Test case Id        TC_K_70_CSMS
Use case Id(s)      n/a
Requirement(s)      n/a
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to set multiple Charging Profiles.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a SetChargingProfileRequest with
    - chargingProfilePurpose TxDefaultProfile
2. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
3. The CSMS sends a SetChargingProfileRequest with
    - chargingProfilePurpose ChargingStationMaxProfile
4. The Test System responds with a SetChargingProfileResponse with
    - status Accepted

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose TxDefaultProfile
    - chargingProfile.chargingProfileKind is Absolute OR Recurring
    - chargingProfile.chargingSchedule.startSchedule must NOT be omitted.
    - If chargingProfile.chargingProfileKind is Recurring then chargingProfile.recurrencyKind must NOT be
      omitted.
* Step 3:
    Message SetChargingProfileRequest
    - chargingProfile.id <different id from chargingProfile at step 1>
    - chargingProfile.chargingProfilePurpose ChargingStationMaxProfile
    - chargingProfile.chargingProfileKind is Absolute
    - chargingProfile.chargingSchedule.startSchedule must NOT be omitted.

The received Charging Profiles must comply with the requirements defined at part 2 specification.

Post scenario validations:
    - N/a
"""
