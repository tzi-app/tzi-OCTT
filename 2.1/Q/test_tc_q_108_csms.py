"""
Test case name      V2X Authorisation - ISO15118-20 - Central V2X control with charging schedule
Test case Id        TC_Q_108_CSMS
Use case Id(s)      Q03
Requirement(s)      Q03.FR.01, Q03.FR.02

Requirement Details:
    Q03.FR.01: CSMS SHALL send a SetChargingProfileRequest message with one or more chargingSchedulePeriod(s)
               that have operationMode = CentralSetpoint.
        Precondition: When CSMS provides setpoints for charging/discharging
    Q03.FR.02: CSMS SHALL provide a value for setpoint.
        Precondition: Q03.FR.01
        Note: This optionally includes the L2 and L3 variants of setpoint
System under test   CSMS

Description         To allow the CSMS to control the charge and discharge behaviour of an EV with power
                    profiles.

Purpose             To verify the CSMS is able to set a charging profile with a setpoint in the ISO15118-20
                    transaction.

Prerequisite(s)     CSMS supports ISO15118-20

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is ISO15118-20 transaction started in V2X AC_BPT energy transfer mode exposing:
                    - <allowedEnergyTransferModes>
                    - <transactionId>

Test Scenario
1. CSMS sends a SetChargingProfileRequest
2. Test System responds with a SetChargingProfileResponse with
    - status Accepted

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfile.transactionId must be <transactionId>
    - chargingProfile.chargingProfilePurpose must be TxProfile
    - chargingProfile.chargingSchedule.chargingRateUnit must be W
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].startPeriod must be 0
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].operationMode must be CentralSetpoint
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].setpoint must be 10.000
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].numberPhases may be present
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].phaseToUse may be present
    - all other fields in chargingProfile.chargingSchedule.chargingSchedulePeriod[0] must be absent

Post scenario validations:
    N/a
"""
