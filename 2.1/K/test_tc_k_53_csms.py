"""
Test case name      Charging with load leveling based on High Level Communication - Success
Test case Id        TC_K_53_CSMS
Use case Id(s)      K15
Requirement(s)      K15.FR.02, K15.FR.03, K15.FR.05, K15.FR.07, K15.FR.11

Requirement Details:
    K15.FR.02: In response to a NotifyEVChargingNeedsRequest the CSMS SHALL send a
               NotifyEVChargingNeedsResponse.
        Precondition: K15.FR.01
    K15.FR.03: If the CSMS is able to provide a charging schedule, it SHALL indicate this by setting the
               status field in the NotifyEVChargingNeedsResponse to Accepted.
        Precondition: K15.FR.02
    K15.FR.05: If the CSMS is able to provide a charging schedule; but needs processing time, it SHALL
               indicate this by setting the status field in the NotifyEVChargingNeedsResponse to Processing.
        Precondition: K15.FR.02
        Note: The Charging Station does not have to wait for the SetChargingProfileRequest. CSMS will send it
              later and trigger a renegotiation as per use case K16.
    K15.FR.07: The CSMS SHALL send a SetChargingProfileRequest with chargingProfilePurpose = TxProfile and a
               transactionId and at most three chargingSchedule and optional salesTariff elements, that each
               contain no more periods than specified by maxScheduleTuples in NotifyEVChargingNeedsRequest and
               by device model variable SmartChargingCtrlr.PeriodsPerSchedule.
        Precondition: K15.FR.03 or K15.FR.05
        Note: The Charging Station will calculate the composite schedule(s) for the EVSE (taking into account
              a ChargingStationMaxProfile or ChargingStationExternalConstraints if present) and will convert
              that to the SAScheduleList format for ISO 15118.
    K15.FR.11: CSMS responds with NotifyEVChargingScheduleResponse with status Accepted to Charging Station.
        Precondition: K15.FR.10 AND EV charging profile is within limits of CSMS ChargingSchedule
        Note: Note: Already checked by Charging Station, but CSMS does its own check.
System under test   CSMS

Description         ISO15118-1 E1 AC Charging with load leveling based on High Level Communication, and E4 DC
                    charging with load leveling based on High Level Communication.

Purpose             To verify if the CSMS is able to perform load leveling when it receives the EV charging
                    needs from the Charging Station.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized
                    State is EVConnectedPreSession

Test Scenario
1. Execute reusable state ISO15118SmartCharging
2. The CSMS does NOT send a SetChargingProfileRequest
    Note(s):
    - The CSMS must NOT initiate a renegotiate after starting the transaction, without cause. For example; a
      smart charging algorithm or an external trigger, etc.

Tool validations
- N/a

Post scenario validations:
    N/a
"""
