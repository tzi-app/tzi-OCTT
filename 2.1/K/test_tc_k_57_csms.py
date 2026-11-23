"""
Test case name      Renegotiating a Charging Schedule ISO 15118-20 - Initiated by EV
Test case Id        TC_K_57_CSMS
Use case Id(s)      K17
Requirement(s)      K17.FR.02, K17.FR.03, K17.FR.05, K17.FR.07, K17.FR.11

Requirement Details:
    K17.FR.02: In response to a NotifyEVChargingNeedsRequest the CSMS SHALL send a
               NotifyEVChargingNeedsResponse.
        Precondition: K17.FR.01
    K17.FR.03: CSMS SHALL indicate this by setting the status field in the NotifyEVChargingNeedsResponse to
               'Accepted'.
        Precondition: K17.FR.02 AND If the CSMS is able to provide a charging schedule now
    K17.FR.05: CSMS SHALL indicate this by setting the status field in the NotifyEVChargingNeedsResponse to
               'Processing'.
        Precondition: K17.FR.02 AND If the CSMS is able to provide a charging schedule, but needs processing
                      time
    K17.FR.07 (2.1): The CSMS SHALL send a SetChargingProfileRequest with chargingProfilePurpose = TxProfile
                     and at most three chargingSchedule and optional price schedule elements, that each
                     contain no more periods than specified by maxScheduleTuples in
                     NotifyEVChargingNeedsRequest and by device model variable
                     SmartChargingCtrlr.PeriodsPerSchedule.
        Precondition: (K17.FR.03 OR K17.FR.05) AND controlMode is ScheduledControl or absent
    K17.FR.11 (2.1): CSMS responds with NotifyEVChargingScheduleResponse with status Accepted to Charging
                     Station.
        Precondition: K17.FR.10 AND EV charging profile is within limits of CSMS ChargingSchedule
        Note: Note: Already checked by Charging Station, but CSMS does its own check. Not applicable in
              dynamic control mode.
System under test   CSMS

Description         The EV signals the Charging Station that it wants to renegotiate and it provides new
                    charging needs, which the Charging Station sends to the CSMS. Based on this and other
                    parameters, the CSMS calculates a new charging schedule and sends it via
                    SetChargingProfileRequest to Charging Station, which communicates it to the EV.

Purpose             To verify if the CSMS is able to renegotiate when the EV signals the Charging Station that
                    it wants to renegotiate and it provides new charging needs, which the Charging Station
                    sends to the CSMS.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is
                    Authorized AND
                    EVConnectedPreSession AND
                    ISO15118SmartCharging

Test Scenario
1. The Test System sends a NotifyEVChargingNeedsRequest.
    With
    - evseId <Configured evseId>
    - maxScheduleTuples & chargingNeeds <Configured values from mock EV>
2. The CSMS responds with a NotifyEVChargingNeedsResponse.
4. The Test System responds with a SetChargingProfileResponse
    With
    - status Accepted
3. The CSMS sends a SetChargingProfileRequest
    Note(s):
    - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
      request
5. The Test System sends a NotifyEVChargingScheduleRequest.
    With
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 3>
6. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 2:
    (Message: NotifyEVChargingNeedsResponse)
    - status Accepted or Processing
* Step 3:
    (Message: SetChargingProfileRequest)
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 6:
    (Message: NotifyEVChargingScheduleResponse)
    - status Accepted

Post scenario validations:
    N/a
"""
