"""
Test case name      ISO 15118-20 Dynamic Control Mode - Success
Test case Id        TC_K_115_CSMS
Use case Id(s)      K17,K19
Requirement(s)      K17.FR.02, K17.FR.03, K17.FR.05, K17.FR.07, K17.FR.08, K17.FR.11, K17.FR.19, K19.FR.02,
                    K19.FR.03, K19.FR.05, K19.FR.07, K19.FR.08

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
    K17.FR.08: The CSMS SHOULD send a SetChargingProfileRequest to the Charging Station within 60 seconds.
        Precondition: K17.FR.01
        Note: This is to satisfy the ISO 15118 ChargeParameterDiscoveryReq timeout.
    K17.FR.11 (2.1): CSMS responds with NotifyEVChargingScheduleResponse with status Accepted to Charging
                     Station.
        Precondition: K17.FR.10 AND EV charging profile is within limits of CSMS ChargingSchedule
        Note: Note: Already checked by Charging Station, but CSMS does its own check. Not applicable in
              dynamic control mode.
    K17.FR.19 (2.1): The CSMS SHALL send a SetChargingProfileRequest with chargingProfilePurpose = TxProfile
                     and a transactionId and one chargingSchedule element with one or more
                     chargingSchedulePeriods, and optionally an absolutePriceSchedule or priceLevelSchedule
                     element, that each contain no more periods than specified by maxScheduleTuples in
                     NotifyEVChargingNeedsRequest and by device model variable
                     SmartChargingCtrlr.PeriodsPerSchedule.
        Precondition: (K17.FR.03 OR K17.FR.05) AND controlMode is DynamicControl
        Note: The Charging Station will calculate the composite schedule for the EVSE (taking into account a
              ChargingStationMaxProfile or ChargingStationExternalConstraints if present).
    K19.FR.02: In response to a NotifyEVChargingNeedsRequest the CSMS SHALL send a
               NotifyEVChargingNeedsResponse.
        Precondition: K19.FR.01
    K19.FR.03: If the CSMS is able to provide a charging schedule, it SHALL indicate this by setting the
               status field in the NotifyEVChargingNeedsResponse to Accepted.
        Precondition: K19.FR.02
    K19.FR.05: If the CSMS is able to provide a charging schedule; but needs processing time, it SHALL
               indicate this by setting the status field in the NotifyEVChargingNeedsResponse to Processing.
        Precondition: K19.FR.02
        Note: The Charging Station does not have to wait for the SetChargingProfileRequest. CSMS will send it
              later and trigger a renegotiation as per use case K16.
    K19.FR.07: The CSMS SHALL send a SetChargingProfileRequest with chargingProfilePurpose = TxProfile and a
               transactionId and one chargingSchedule element with one or more chargingSchedulePeriods, and
               optionally an absolutePriceSchedule or priceLevelSchedule element, that in total contain no
               more periods than specified by maxScheduleTuples in NotifyEVChargingNeedsRequest and by device
               model variable SmartChargingCtrlr.PeriodsPerSchedule.
        Precondition: K19.FR.01 AND ( K19.FR.03 OR K19.FR.05 )
        Note: The Charging Station will calculate the composite schedule for the EVSE (taking into account a
              ChargingStationMaxProfile or ChargingStationExternalConstraints if present). maxScheduleTuples
              provides a maximum for charging schedule periods, price schedule entries and price rules. (see
              ISO 15118-20 [V2G20-2175]).
    K19.FR.08: The CSMS SHOULD send a SetChargingProfileRequest to the Charging Station within 60 seconds.
        Precondition: K19.FR.01
        Note: This is to satisfy the ISO 15118-20 ScheduleExchangeReq timeout.
System under test   CSMS

Description         The EV signals the Charging Station that it wants to renegotiate and it provides new
                    charging needs, which the Charging Station sends to the CSMS. Based on this and other
                    parameters, the CSMS calculates a new charging schedule and sends it via
                    SetChargingProfileRequest to Charging Station, which communicates it to the EV.

Purpose             To verify if the CSMS is able to renegotiate when the EV signals the Charging Station that
                    it wants to renegotiate for DynamicControl and it provides new charging needs, which the
                    Charging Station sends to the CSMS.

Prerequisite(s)     CSMS supports ISO 15118-20.

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized
                    State is EVConnectedPreSession

Test Scenario
1. The Test System sends a NotifyEVChargingNeedsRequest with
    - evseId <Configured evseId>
    - maxScheduleTuples 3
    - chargingNeeds.requestedEnergyTransfer AC_BPT
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
    - chargingNeeds.controlMode DynamicControl
    - chargingNeeds.v2xChargingParameters.maxChargePower 5000
    - chargingNeeds.v2xChargingParameters.maxDischargePower 5000
2. The CSMS responds with a NotifyEVChargingNeedsResponse.
3. The CSMS sends a SetChargingProfileRequest
    Note(s):
    - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
      request
4. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
5. The Test System sends a NotifyEVChargingScheduleRequest with
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 3>
6. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 2:
    Message: NotifyEVChargingNeedsResponse
    - status must be Accepted or Processing
* Step 3:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfilePurpose must be TxProfile
    - transactionId must be <Provided transactionId from before>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriods must be size <= 3
    - chargingProfile.chargingSchedule[*].absolutePriceSchedule.priceRuleStacks must be size <= 3
    - chargingProfile.chargingSchedule[*].priceLevelSchedule.priceLevelScheduleEntries must be size <= 3
* Step 6:
    Message: NotifyEVChargingScheduleResponse
    - status must be Accepted

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.17. Page 392 - (2026-06) - K18.FR.17/K19.FR.13 InvalidMessageSequence must be InvalidMessageSeq
        (Part 2 errata - applies to this test via use case K19)
        Requirements K18.FR.17 and K19.FR.13 refer to a reasonCode InvalidMessageSequence. This must be
        InvalidMessageSeq.

        Changed requirements

        | ID | Precondition | Requirements | Note |
        | K18.FR.17 | When Charging Station receives a SetChargingProfileRequest immediately after the
          transaction has started and before it has sent the NotifyEVChargingNeedsRequest to CSMS | The
          Charging Station SHOULD respond with SetChargingProfileResponse with status = Rejected and a
          statusInfo with reasonCode= "InvalidMessageSeq". | CSMS sent profile too early. It does not harm if
          CS accepts the charging profile instead of rejecting it, as long as it sends a charging profile
          again when it receives the NotifyEVChargingNeedsRequest. |
        | K19.FR.13 | When Charging Station receives a SetChargingProfileRequest immediately after the
          transaction has started and before it has sent the NotifyEVChargingNeedsRequest to CSMS | The
          Charging Station SHOULD respond with SetChargingProfileResponse with status = Rejected and a
          statusInfo with reasonCode= "InvalidMessageSeq". | CSMS sent profile too early. It does not harm if
          CS accepts the charging profile instead of rejecting it, as long as it sends a charging profile
          again when it receives the NotifyEVChargingNeedsRequest. |
"""
