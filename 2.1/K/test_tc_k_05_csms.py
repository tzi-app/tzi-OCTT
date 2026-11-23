"""
Test case name      Clear Charging Profile - With chargingProfileId
Test case Id        TC_K_05_CSMS
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
                    profile (not TxDefault) with only a chargingProfileId as described at the OCPP
                    specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        CSMS sends a GetChargingProfilesRequest
                    Test System responds with a GetChargingProfilesResponse with status Accepted
                    Test System sends a ReportChargingProfilesRequest
                    CSMS responds with a ReportChargingProfilesResponse

Reusable State      N/a

Test Scenario
1. The CSMS sends a ClearChargingProfileRequest with
    - chargingProfileId <Generated chargingProfileId> AND
    - chargingProfileCriteria omit
2. The Test System responds with a ClearChargingProfileResponse with status Accepted

Tool validations
* Step 1:
    Message ClearChargingProfileRequest
    - chargingProfileId <Generated chargingProfileId> AND
    - chargingProfileCriteria omit

Post scenario validations:
    - N/a
"""
