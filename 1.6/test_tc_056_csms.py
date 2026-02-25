"""
Test case name      Central Smart Charging - TxDefaultProfile
Test case Id        TC_056_CSMS
Feature profile     SmartCharging

Reference           CompliancyTestTool-TestCaseDocument, Table 178, page 151,
                    section 3.19.1 Central Smart Charging

Description         The Central System sets a default schedule for new transactions.
Purpose             To check whether the Central System can set a default schedule for new transactions.
Prerequisite(s)     The Central System supports the Smart Charging feature profile.

Before State:
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
    1. The Central System sends a SetChargingProfile.req to the Charge Point.
    2. The Charge Point responds with a SetChargingProfile.conf.

Tool validations
    * Step 1:
        (Message: SetChargingProfile.req)
        - connectorId should be <Configured connectorId>
        - csChargingProfiles.stackLevel should be <Configured stackLevel>
        - csChargingProfiles.chargingProfilePurpose should be TxDefaultProfile
        - csChargingProfiles.chargingProfileKind should be Absolute
        - csChargingProfiles.validFrom should be present (Not omitted)
        - csChargingProfiles.validTo should be present (Not omitted)
        - csChargingProfiles.transactionId should be omitted
        - csChargingProfiles.recurrencyKind should be omitted
        - csChargingProfiles.chargingSchedule.startSchedule should be present (Not omitted)
        - csChargingProfiles.chargingSchedule.chargingRateUnit should be <Configured chargingRateUnit>
        - csChargingProfiles.chargingSchedule.duration should be <Configured duration>
        - csChargingProfiles.chargingSchedule.chargingSchedulePeriod.startPeriod should be <Configured startPeriod>
        - csChargingProfiles.chargingSchedule.chargingSchedulePeriod.limit should be 6.0 or 6000.0
        - csChargingProfiles.chargingSchedule.chargingSchedulePeriod.numberPhases:
            If <Configured numberPhases> is NOT 3: numberPhases should be <Configured numberPhases>
            If <Configured numberPhases> IS 3: numberPhases should be <Configured numberPhases> or omitted

    * Step 2:
        (Message: SetChargingProfile.conf)
        - status should be Accepted

Expected result(s) / behaviour: n/a
"""
