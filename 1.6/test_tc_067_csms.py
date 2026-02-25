"""
Test case name      Clear Charging Profile
Test case Id        TC_067_CSMS
Feature profile     SmartCharging (Section 3.19)
Document reference  Table 181, Section 3.19.3, Pages 154-155/176

Description         The Central System sets a Charging Profile and clears it.
Purpose             To check whether the Central System can clear a charging profile.
Prerequisite(s)     The Central System supports the Smart Charging feature profile.

Before State:
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): Charging
        NOTE: "Charging" references a reusable state (a transaction must be running
        on the Charge Point). Exact reusable state definition to be verified.

System under test   Central System

Test Scenario
    Manual Action: Set three different charging profiles. Steps 1-2 are therefor repeated three times.
    1. The Central System sends a SetChargingProfile.req to the Charge Point.
    2. The Charge Point responds with a SetChargingProfile.conf.
    (Repeated 3 times for 3 different charging profiles)

    Manual Action: Clear a charging profile based on ID.
    3. The Central System sends a ClearChargingProfile.req to the Charge Point.
    4. The Charge Point responds with a ClearChargingProfile.conf.

    Manual Action: Clear a charging profile based on criteria.
    5. The Central System sends a ClearChargingProfile.req to the Charge Point.
    6. The Charge Point responds with a ClearChargingProfile.conf.

    Manual Action: Clear all remaining charging profiles.
    7. The Central System sends a ClearChargingProfile.req to the Charge Point.
    8. The Charge Point responds with a ClearChargingProfile.conf.

Tool validations
    * Step 1 (SetChargingProfile.req) - Three charging profiles are set:
        Charging profile 1:
            - connectorId should be 0
            - chargingProfilePurpose should be ChargePointMaxProfile
            - stackLevel should be <Configured Stack Level>
            - transactionId should be <Omitted>
            - chargingProfileId should be <Different than the chargingProfileId from profile 2 and 3>

        Charging profile 2:
            - connectorId should be <Configured ConnectorId>
            - chargingProfilePurpose should be TxDefaultProfile
            - stackLevel should be <Configured Stack Level>
            - transactionId should be <Omitted>
            - chargingProfileId should be <Different than the chargingProfileId from profile 1 and 3>

        Charging profile 3:
            - connectorId should be <Configured ConnectorId>
            - chargingProfilePurpose should be TxProfile
            - stackLevel should be <Configured Stack Level>
            - transactionId should be <Generated transactionId by Central System>
            - chargingProfileId should be <Different than the chargingProfileId from profile 1 and 2>

    * Step 2 (SetChargingProfile.conf) - for each of the 3 profiles:
        - status should be Accepted

    * Step 3 (ClearChargingProfile.req) - Clear by ID:
        - id should be <Generated Id from charging profile 1>
        - connectorId, chargingProfilePurpose, and stackLevel fields should be omitted

    * Step 4/6/8 (ClearChargingProfile.conf):
        - status should be Accepted

    * Step 5 (ClearChargingProfile.req) - Clear by criteria:
        - id should be omitted
        - connectorId should be <Configured ConnectorId>
        - chargingProfilePurpose should be TxDefaultProfile
        - stackLevel should be <Configured Stack Level>

    * Step 7 (ClearChargingProfile.req) - Clear all remaining:
        - All fields should be omitted

Expected result(s) / behaviour:
    Charge Point (Tool): n/a
    Central System (SUT): The Central System was able to clear the ChargingProfile of the Charge Point.
"""
