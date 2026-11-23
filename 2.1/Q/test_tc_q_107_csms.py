"""
Test case name      V2X Authorisation - ISO15118-20 - Charging only (V2X control) before starting V2X
Test case Id        TC_Q_107_CSMS
Use case Id(s)      Q02
Requirement(s)      Q02.FR.01, Q02.FR.02, Q02.FR.05

Requirement Details:
    Q02.FR.01: CSMS SHALL send a SetChargingProfileRequest message, with chargingSchedulePeriod(s) with field
               operationMode set to ChargingOnly or omitted
        Precondition: When Charging Station does not request bidirectional power transfer in
                      NotifyEVChargingNeedsRequest
        Note: When operationMode is omitted, this also defaults to ChargingOnly.
    Q02.FR.02: CSMS SHALL NOT include fields dischargeLimit, setpoint, setpointReactive in the
               ChargingProfileType.
        Precondition: Q02.FR.01
        Note: This also includes the L2 and L3 variants of those fields.
    Q02.FR.05: CSMS SHALL send a NotifyAllowedEnergyTransferRequest with the allowedEnergyTransfer list and
               with transactionId set to the transaction for which this is intended.
        Precondition: When CSMS changes the list of allowed energy transfers for a transaction
        Note: For example, when permission for V2X is received some time after authorization.
System under test   CSMS

Description         To start a transaction with operationMode ChargingOnly, such that it can become a
                    bidirectional session at a later time.

Purpose             To check if the CSMS supports starting in a non-bidirectional way.

Prerequisite(s)     CSMS supports ISO15118-20

Configuration State - CSMS is configured to start transactions first in a non-V2X mode before upgrading to V2X

Memory State        N/a

Reusable State(s)   State is ISO15118-20 transaction just started exposing:
                    - <allowedEnergyTransferModes>
                    - <transactionId>

Test Scenario
Agree on energy transfer mode
1. The Test System sends a NotifyEVChargingNeedsRequest with
    - evseId <Configured evseId>
    - chargingNeeds.requestedEnergyTransfer one of non-bidirectional mode in <allowedEnergyTransferModes>
      received in AuthorizeResponse or if omitted AC_three_phase
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_two_phase, AC_three_phase, AC_BPT,
      AC_BPT_DER, AC_DER]
    - chargingNeeds.controlMode ScheduledControl
    - chargingNeeds.v2xChargingParameters.maxChargePower 1234W
    - chargingNeeds.v2xChargingParameters.maxDischargePower 1234W
2. The CSMS responds with a NotifyEVChargingNeedsResponse

Setting charging profile
3. The CSMS sends a SetChargingProfileRequest
4. The Test System responds with a SetChargingProfileResponse with
    - status Accepted

Manual Action: Trigger CSMS to allow V2X after initial start

5. The CSMS sends a NotifyAllowedEnergyTransferRequest
6. The Test System sends a NotifyAllowedEnergyTransferResponse with

Tool validations
* Step 2:
    Message: NotifyEVChargingNeedsResponse
    - status must be Accepted or Processing
* Step 3:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfile.transactionId must be <transactionId>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].operationMode must be ChargingOnly |
      <omitted>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].dischargeLimit must be <omitted> | <empty>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].dischargeLimit_L2 must be <omitted> |
      <empty>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].dischargeLimit_L3 must be <omitted> |
      <empty>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setpoint must be <omitted> | <empty>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setpoint_L2 must be <omitted> | <empty>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setpoint_L3 must be <omitted> | <empty>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setPointReactive must be <omitted> |
      <empty>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setPointReactive_L2 must be <omitted> |
      <empty>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setPointReactive_L3 must be <omitted> |
      <empty>
* Step 5:
    Message: NotifyAllowedEnergyTransferRequest
    - transactionId must be <transactionId>
    - allowedEnergyTransfer must contain one of [DC_BPT, AC_BPT, AC_BPT_DER]

Post scenario validations:
    N/a

Remarks
Transcription note: in the source PDF, step 6 ends with the word "with" and no parameters follow it (the Main
                    table ends there at the bottom of page 1339). It is transcribed as printed.

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.21. Page 511 - (2026-09) - Q01.FR.02 - EVCCID not known at start when using EIM [1317] - 2.21.2. Page
        512 - Use case Q02 - Update of scenario description
        (Part 2 errata - applies to this test via use case Q02)
        Similarly to the situation in Q01 described above, the EVCCID may not be known yet at authorization
        time. The scenario description has been updated to allow for this by making EVCCID optional in the
        AuthorizeRequest and allow to get it later in a TransactionEventRequest.

        | No. | Type | Description |
        | 1 | Name | Starting in operationMode ChargingOnly before enabling V2X |
        | 2 | ID | Q02 |
        | 3 | Objective(s) | … |
        | 4 | Description | … |
        |  | Actors | EV, Charging Station, CSMS |

        | No. | Type | Description |
        |  | Scenario description | 1. The Charging Station sends a [authorizerequest] with optionally the
          EVCCID of EV in additionalInfo of idToken if already known. / &nbsp;&nbsp;&nbsp;&nbsp;a. The CSMS
          cannot (yet) allow V2X and returns an [authorizeresponse] with idTokenInfo.status = Accepted and
          omits the field allowedEnergyTransfer. / 2. The Charging Station sends a
          [notifyevchargingneedsrequest] with requestedEnergyTransfer set to normal AC or DC. / 3. The CSMS
          will respond with the [notifyevchargingneedsresponse] message, with status set to Accepted / 4. The
          CSMS sends a [setchargingprofilerequest] message, with a chargingSchedule with operationMode set to
          ChargingOnly. / &nbsp;&nbsp;&nbsp;&nbsp;a. Charging Station and CSMS behave as described in
          [k_use_cases]. / 5. The CSMS gets the EVCCID from EV from additionalInfo which it had received in
          the [authorizerequest] ,a [transactioneventrequest] , or from the device model variable
          ConnectedEV.VehicleId. / 6. Alternatively, CSMS gets the vehicle certificate from the device model
          variable ConnectedEV.VehicleCertificate. / 7. When CSMS decides to allow V2X, for example based on
          idToken, EVCCID or vehicle certificate / &nbsp;&nbsp;&nbsp;&nbsp;a. CSMS sends a
          [notifyallowedenergytransferrequest] to Charging Station with an updated allowedEnergyTransfer list
          that contains a bidirectional transfer, DC_BPT, AC_BPT or AC_BPT_DER. / &nbsp;&nbsp;&nbsp;&nbsp;b.
          Charging Station responds with [notifyallowedenergytransferresponse] with status = Accepted. / 8.
          The Charging Station will start a service renegotiation with the EV, allowing the EV to change its
          current energy service to one with potentially more value. |
        | 5 | Prerequisites |  |
        | … | … | … |

    6.3.20. Page 1339/1340 - (2026-02) - TC_Q_107_CSMS - Test case updated
        Test case updated to reflect current use cases and functional requirements.

        | Test case name | V2X Authorisation - ISO15118-20 - Charging only (V2X control) before starting V2X |
        | Test case Id | TC_Q_107_CSMS |
        | … | |

        | Before (Preparations) |
        | Configuration State: / [removed: - CSMS is configured to start transactions first in a non-V2X mode
          before upgrading to V2X] / N/a |
        | Memory State: / N/a |
        | Reusable State(s): / State is ISO15118-20 transaction just started exposing: / -
          <allowedEnergyTransferModes> / - <transactionId> |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | Agree on energy transfer mode | |
        | 1. The Test System sends a NotifyEVChargingNeedsRequest with / evseId <Configured evseId> /
          chargingNeeds.requestedEnergyTransfer one of non-bidirectional mode in <allowedEnergyTransferModes>
          received in AuthorizeResponse or if omitted AC_three_phase / chargingNeeds.availableEnergyTransfer
          [AC_single_phase, AC_two_phase, AC_three_phase, AC_BPT, AC_BPT_DER, AC_DER] /
          chargingNeeds.controlMode ScheduledControl / chargingNeeds.v2xChargingParameters.maxChargePower
          1234W / chargingNeeds.v2xChargingParameters.maxDischargePower 1234W | 2. The CSMS responds with a
          NotifyEVChargingNeedsResponse |
        | Setting charging profile | |
        | 4. The Test System responds with a SetChargingProfileResponse with / status Accepted | 3. The CSMS
          sends a SetChargingProfileRequest |
        | Manual Action: Trigger CSMS to allow V2X after initial start | |
        | 6. The Test System sends a NotifyAllowedEnergyTransferResponse with / status Accepted | 5. The CSMS
          sends a NotifyAllowedEnergyTransferRequest |
        | 7. The Test System sends a NotifyEVChargingNeedsRequest with / evseId <Configured evseId> /
          chargingNeeds.requestedEnergyTransfer one of bidirectional mode in <allowedEnergyTransferModes>
          received in NotifyAllowedEnergyTransferRequest / chargingNeeds.availableEnergyTransfer
          [AC_single_phase, AC_two_phase, AC_three_phase, AC_BPT, AC_BPT_DER, AC_DER] /
          chargingNeeds.controlMode ScheduledControl / chargingNeeds.v2xChargingParameters.maxChargePower
          1234W / chargingNeeds.v2xChargingParameters.maxDischargePower 1234W | 8. The CSMS responds with a
          NotifyEVChargingNeedsResponse |
        | Setting charging profile | |
        | 10. The Test System responds with a SetChargingProfileResponse with / status Accepted | 9. The CSMS
          sends a SetChargingProfileRequest |

        | Main (Test scenario) | |
        | 11. The Test System sends a TransactionEventRequest with / eventType Updated / triggerReason
          OperationModeChanged / transactionInfo.transactionId <transactionId> / transactionInfo.operationMode
          <Operation mode from step 9> | 12. The CSMS responds with a TransactionEventResponse |

        | Tool validations |
        | \\* Step 2: / Message: NotifyEVChargingNeedsResponse / - status must be Accepted or Processing / \\*
          Step 3: / Message: SetChargingProfileRequest / - evseId must be <Configured evseId> / -
          chargingProfile.transactionId must be <transactionId> / -
          chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].operationMode must be ChargingOnly |
          <omitted> / - chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].Limit must NOT be
          <omitted> | <empty> / - chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].dischargeLimit
          must be <omitted> | <empty> / -
          chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].dischargeLimit_L2 must be <omitted> |
          <empty> / - chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].dischargeLimit_L3 must be
          <omitted> | <empty> / - chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].setpoint must
          be <omitted> | <empty> / - chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].setpoint_L2
          must be <omitted> | <empty> / -
          chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].setpoint_L3 must be <omitted> |
          <empty> / - chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].setPointReactive must be
          <omitted> | <empty> / -
          chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].setPointReactive_L2 must be <omitted>
          | <empty> / - chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].setPointReactive_L3 must
          be <omitted> | <empty> / \\* Step 5: / Message: NotifyAllowedEnergyTransferRequest / - transactionId
          must be <transactionId> / - allowedEnergyTransfer must contain one of [DC_BPT, AC_BPT, AC_BPT_DER] /
          \\* Step 7: / Message: NotifyEVChargingNeedsResponse / - status must be Accepted or Processing / \\*
          Step 9: / Message: SetChargingProfileRequest / - evseId must be <Configured evseId> / -
          chargingProfile.transactionId must be <transactionId> / -
          chargingProfile.chargingSchedule[\\].chargingSchedulePeriod[\\].operationMode must NOT be ChargingOnly
          | <empty> |
        | Post scenario validations: / N/a |
"""
