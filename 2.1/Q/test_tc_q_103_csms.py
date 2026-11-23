"""
Test case name      V2X Authorisation - ISO15118-20 - Charging needs rejected
Test case Id        TC_Q_103_CSMS
Use case Id(s)      Q01
Requirement(s)      Q01.FR.04

Requirement Details:
    Q01.FR.04: CSMS SHALL respond with a NotifyEVChargingNeedsResponse with status = Rejected.
        Precondition: If CSMS does not accept the requestedEnergyTransfer
System under test   CSMS

Description         Authorization of an EV by the CSMS to start a V2X power transfer loop.

Purpose             To check if the CSMS rejects a NotifyEVChargingNeedsRequest when the EV requests a
                    EnergyTransferModes that is not allowed.

Prerequisite(s)     CSMS supports ISO15118-20

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is ISO15118-20 transaction just started exposing:
                    - <allowedEnergyTransferModes>
                    - <transactionId>

Test Scenario
Agree on energy transfer mode

1. Test System sends a NotifyEVChargingNeedsRequest with
    - evseId <Configured evseId>
    - chargingNeeds.requestedEnergyTransfer one different than mentioned in <allowedEnergyTransferModes> or if
      omitted AC_BPT
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_two_phase, AC_three_phase, AC_BPT,
      AC_BPT_DER, AC_DER]
    - chargingNeeds.controlMode ScheduledControl
    - chargingNeeds.v2xChargingParameters.maxChargePower 1234W
    - chargingNeeds.v2xChargingParameters.maxDischargePower 0W
2. CSMS SHALL respond with a NotifyEVChargingNeedsResponse

Tool validations
* Step 2:
    Message: NotifyEVChargingNeedsResponse
    - status must be Rejected

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.21. Page 511 - (2026-09) - Q01.FR.02 - EVCCID not known at start when using EIM [1317] - 2.21.1. Page
        509 - Use case Q01 - Update of remark
        (Part 2 errata - applies to this test via use case Q01)
        When authorization is not done via PnC, but via External Identification Means (EIM) the existing
        requirement to send EVCCID in the "Started" event may not work because a transaction can be started
        before ISO 15118 communication is active.

        The requirement has been adapted to fix this.

        |  | ID. | Precondition | Requirements | Note |
        | Old | Q01.FR.02 | When Charging Station’s ISO15118Ctrlr.Enabled = true and V2XChargingCtrlr.Enabled
          = true / AND / Charging Station starts an ISO 15118-20 transaction | Charging Station SHALL add
          EVCCID to idToken in [transactioneventrequest](eventType=Started) in
          idToken.additionalInfo.additionalIdToken and with idToken.additionalInfo.type set to "EVCCID". |
          This transaction may become bidirectional. This is needed in case CSMS uses the EVCCID of vehicle to
          decide whether to allow V2X. |
        | New | Q01.FR.02 | When Charging Station’s ISO15118Ctrlr.Enabled = true and V2XChargingCtrlr.Enabled
          = true / AND / Charging Station starts an ISO 15118-20 transaction | Charging Station SHALL add
          EVCCID in the first TransactionEventRequest that occurs after Charging Station received the EVCCID
          from EV by providing it as part of the idToken in idToken.additionalInfo.additionalIdToken with
          idToken.additionalInfo.type set to "EVCCID” | This may result in the idToken being sent for the
          second time. EVCCID is needed in case CSMS uses it to decide whether to allow V2X if requested. |

        The remark of use case Q01 has been updated to make clear that the EVCCID is presented in a
        TransactionEvent and also present in the ConnectedEV component.

        | No. | Type | Description |
        | 1 | Name | V2X Authorization |
        | 2 | ID | Q01 |
        | … | … | … |
        | 8 | Remarks | … / The EVCCID will be presented in a TransactionEventRequest as the additionalInfo
          field of the idToken . / The ISO 15118 EVCCID of the EV is also made available in the device model
          as the variable VehicleId from the component ConnectedEV.[removed: , if that is needed by the
          operator to determine whether to allow V2X operations.] / In some cases the EVCCID may be used as an
          idToken for authorization. [removed: , or it can be added to the additionalInfo field of the idToken
          that is used for authorization.] |

    2.21. Page 511 - (2026-09) - Q01.FR.02 - EVCCID not known at start when using EIM [1317] - 2.21.2. Page
        512 - Use case Q02 - Update of scenario description
        (Part 2 errata - applies to this test via use case Q01)
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

    2.21. Page 511 - (2026-09) - Q01.FR.02 - EVCCID not known at start when using EIM [1317] - 2.21.3. Page
        163 - Added EVCCID to E 1.5. Clarification for optional fields
        (Part 2 errata - applies to this test via use case Q01)
        idToken

        (E03.FR.01) The field idToken is provided once in the first TransactionEventRequest that occurs after
        the transaction has been authorized.
        (E07.FR.02) The field idToken is provided once in the TransactionEventRequest that occurs when the
        authorization of the transaction has been ended.
        (C12.FR.02) The above is also the case when authorization was granted because the idToken is present
        in the authorization cache with a Accepted status.
        (F02.FR.05): The above is also the case when the idToken is provided by a
        RequestStartTransactionRequest.
        (Q01.FR.02) The field idToken is provided (again) with the EVCCID in
        idToken.additionalInfo.additionalIdToken .
"""
