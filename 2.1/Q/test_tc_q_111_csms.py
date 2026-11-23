"""
Test case name      External V2X control - with a charging profile from CSMS - setpoint
Test case Id        TC_Q_111_CSMS
Use case Id(s)      Q05
Requirement(s)      …
System under test   CSMS

Description         CSMS explicitly allows an External System to control the charge and discharge behaviour of
                    an EV for a certain period of time.

Purpose             To verify if the CSMS is able to configure the CS to use an External V2X setpoint with
                    relative or dynamic charging profile.

Prerequisite(s)     - CSMS supports Bidirectional Power Transfer

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual action: trigger CSMS to set a TxDefaultProfile, Relative Charging Profile with chargingSchedulePeriod
               with operationMode ExternalSetpoint

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with status Accepted

Manual action: trigger CSMS to set a TxDefaultProfile, Dynamic Charging Profile with chargingSchedulePeriod
               with operationMode ExternalSetpoint

3. The CSMS sends a SetChargingProfileRequest
4. The Test System responds with a SetChargingProfileResponse with status Accepted

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfile.chargingProfilePurpose must be TxDefaultProfile
    - chargingProfile.chargingProfileKind Relative
    - chargingProfile.dynUpdateTime must be <omitted>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].operationMode must be ExternalSetpoint
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setpoint must be <not omitted>
* Step 3:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfile.chargingProfilePurpose must be TxDefaultProfile
    - chargingProfile.chargingProfileKind Dynamic
    - chargingProfile.dynUpdateTime must be <Datetime of moment of step 3>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].operationMode must be ExternalSetpoint
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setpoint must be <not omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod size must be 1
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].startPeriod must be 0

Post scenario validations:
    N/a
"""
