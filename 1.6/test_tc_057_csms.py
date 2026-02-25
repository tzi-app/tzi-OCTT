"""
Test case name      Central Smart Charging - TxProfile
Test case Id        TC_057_CSMS
Feature profile     SmartCharging

Document ref        Table 179, pages 152-153/176 (CompliancyTestTool-TestCaseDocument)

Description         The Central System sets a schedule for a running transaction.
Purpose             To check whether the Central System is able to set a schedule for a running transaction on a Charge Point.
Prerequisite(s)     The Central System supports the Smart Charging feature profile.

Before State:
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): Charging
        NOTE: "Charging" refers to a reusable state defined elsewhere in the document (to be resolved later).
              Implies a transaction must be running on the Charge Point.

System under test   Central System

Test Scenario
    1. The Central System sends a SetChargingProfile.req to the Charge Point.
    2. The Charge Point responds with a SetChargingProfile.conf.

Tool validations
    * Step 1:
        (Message: SetChargingProfile.req)
        - connectorId should be <Configured connectorId>
        - csChargingProfiles.chargingProfilePurpose should be TxProfile
        - csChargingProfiles.transactionId should be <Generated transactionId>
        - csChargingProfiles.recurrencyKind should be <Omitted>
        - csChargingProfiles.chargingProfileKind should be Absolute or Relative

        If csChargingProfiles.chargingProfileKind is Absolute:
            - csChargingProfiles.validFrom should be <Not omitted>
            - csChargingProfiles.validTo should be <Not omitted>
            - csChargingProfiles.chargingSchedule.startSchedule should be <Not omitted>
            - csChargingProfiles.chargingSchedule.duration should be <Not omitted>

        If csChargingProfiles.chargingProfileKind is Relative:
            - csChargingProfiles.chargingSchedule.startSchedule should be <Omitted>

    * Step 2:
        (Message: SetChargingProfile.conf)
        - status should be Accepted

Expected result(s) / behaviour: n/a
"""
