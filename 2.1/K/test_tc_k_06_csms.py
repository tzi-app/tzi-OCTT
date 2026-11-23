"""
Test case name      Clear Charging Profile - With stackLevel/purpose combination for one profile
Test case Id        TC_K_06_CSMS
Use case Id(s)      K10
Requirement(s)      K10.FR.02

Requirement Details:
    K10.FR.02: The CSMS SHALL either specify a chargingProfile.id OR include one or more of the fields
               stackLevel, evseId and chargingProfilePurpose in the ClearChargingProfileRequest to specify
               which Charging Profiles need to be cleared.
System under test   CSMS

Description         If the CSMS wishes to clear some or all of the charging profiles that were previously sent
                    to the Charging Station, then the CSMS sends a ClearChargingProfileRequest to the Charging
                    Station.

Purpose             To verify if the CSMS is able to request the charging station to clear a specific charging
                    profile with a stackLevel/purpose combination for a chargingProfileId as described at the
                    OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a ClearChargingProfileRequest with
    - chargingProfilePurpose TxDefaultProfile AND
    - evseId <Configured evseId> AND
    - stackLevel <Configured stackLevel>
2. The Test System responds with a ClearChargingProfileResponse with status Accepted

Tool validations
* Step 1:
    Message ClearChargingProfileRequest
    - chargingProfileCriteria.chargingProfilePurpose TxDefaultProfile AND
    - chargingProfileCriteria.stackLevel <Configured stackLevel> AND
    - chargingProfileCriteria.evseId <Configured evseId> AND
    - chargingProfileId must be omitted.

Post scenario validations:
    - N/a
"""
