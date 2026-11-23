"""
Test case name      Renegotiating a Charging Schedule ISO 15118-20 - Initiated by CSMS
Test case Id        TC_K_113_CSMS
Use case Id(s)      K16
Requirement(s)      K16.FR.06

Requirement Details:
    K16.FR.06: CSMS responds with NotifyEVChargingScheduleResponse with status Accepted to Charging Station.
        Precondition: K16.FR.05 AND EV charging profile is within limits of CSMS ChargingSchedule
        Note: Note: Already checked by Charging Station, but CSMS does its own check.
System under test   CSMS

Description         The CSMS sends a SetChargingProfileRequest to the Charging Station to influence the power
                    or current drawn by the EV. The CSMS calculates a ChargingSchedule to stay within limits
                    which MAY be imposed by an external system.

Purpose             To verify if the CSMS is able to renegotiate power/current drawn by the EV.

Prerequisite(s)     CSMS supports ISO 15118-20

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized
                    State is EVConnectedPreSession
                    State is ISO15118SmartCharging (iso15118-20)

Test Scenario
Manual Action: Trigger SetChargingProfile
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse
    - With status Accepted
3. The Test System sends a NotifyEVChargingScheduleRequest.
    - With evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 1>
4. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 1:
    (Message: SetChargingProfileRequest)
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 4:
    (Message: NotifyEVChargingScheduleResponse)
    - status Accepted

Post scenario validations:
    N/a
"""
