"""
Test case name      Get Composite Schedule
Test case Id        TC_066_CSMS
Feature profile     SmartCharging
Reference           OCTT TestCaseDocument Section 3.19.2, Table 180, Page 153/176

Description         The Central System requests a composite schedule.
Purpose             To check whether the Central System is able to request a composite schedule.
Prerequisite(s)     The Central System supports the Smart Charging feature profile.

Before State:
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
    1. The Central System sends a GetCompositeSchedule.req to the Charge Point.
    2. The Charge Point responds with a GetCompositeSchedule.conf containing a hard-coded composite schedule.

Tool validations
    * Step 1:
        (Message: GetCompositeSchedule.req)
        - connectorId should be <Configured ConnectorId>
        - duration should be <Configured Charging Schedule Duration>
        - chargingRateUnit should be <Configured Charging Rate Unit>

    * Step 2:
        (Message: GetCompositeSchedule.conf)
        - chargingSchedule contains a hard-coded composite schedule

Expected result(s):
    The Central System has retrieved the composite ChargingProfile.

Post scenario validations: N/a
"""
