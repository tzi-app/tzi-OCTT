"""
Test case name      Renegotiating a Charging Schedule ISO 15118-2 - Initiated by CSMS - Send
                    NotifyEVChargingNeeds
Test case Id        TC_K_59_CSMS
Use case Id(s)      K16
Requirement(s)      K16.FR.12

Requirement Details:
    K16.FR.12: The CSMS SHALL send a SetChargingProfileRequest.
        Precondition: K16.FR.09 AND Charging Station sends a NotifyEVChargingNeedsRequest
        Note: This situation is not desirable, because charging profile will likely be the same as in
              K16.FR.01, but this is added for robustness when Charging Station is not adhering to K16.FR.09.
System under test   CSMS

Description         The CSMS sends a SetChargingProfileRequest to the Charging Station to influence the power
                    or current drawn by the EV. The CSMS calculates a ChargingSchedule to stay within limits
                    which MAY be imposed by an external system.

Purpose             To verify if the CSMS is able to handle a Charging Stations resending the charging needs
                    of the EV.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is
                    Authorized AND
                    EVConnectedPreSession AND
                    ISO15118SmartCharging

Test Scenario
Manual Action: Trigger SetChargingProfile
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse
    - With status Accepted
3. The Test System sends a NotifyEVChargingNeedsRequest.
    - With evseId <Configured evseId>
    - maxScheduleTuples & chargingNeeds <Configured values from mock EV>
4. The CSMS responds with a NotifyEVChargingNeedsResponse.
5. The CSMS sends a SetChargingProfileRequest
    Note(s):
    - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
      request
6. The Test System responds with a SetChargingProfileResponse
    - With status Accepted
7. The Test System sends a NotifyEVChargingScheduleRequest.
    - With evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 3>
8. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 1:
    (Message: SetChargingProfileRequest)
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 4:
    (Message: NotifyEVChargingNeedsResponse)
    - status Accepted or Processing
* Step 5:
    (Message: SetChargingProfileRequest)
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 8:
    (Message: NotifyEVChargingScheduleResponse)
    - status Accepted

Post scenario validations:
    N/a

Remarks
The section heading is printed as "TC_K_59_CSMS: Renegotiating a Charging Schedule ISO 15118-20 - Initiated by
CSMS - Send NotifyEVChargingNeeds" (ISO 15118-20), while the Test case name cell is printed with "ISO
15118-2".
"""
