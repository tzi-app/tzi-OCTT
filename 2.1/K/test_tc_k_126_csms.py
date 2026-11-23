"""
Test case name      ISO 15118-20 Dynamic Control Mode - Sets no charging profile
Test case Id        TC_K_126_CSMS
Use case Id(s)      K19
Requirement(s)      K19.FR.02, K19.FR.04

Requirement Details:
    K19.FR.02: In response to a NotifyEVChargingNeedsRequest the CSMS SHALL send a
               NotifyEVChargingNeedsResponse.
        Precondition: K19.FR.01
    K19.FR.04: If the CSMS is not going to provide a charging schedule, it SHALL indicate this by setting the
               status field in the NotifyEVChargingNeedsResponse to NoChargingProfile.
        Precondition: K19.FR.02
        Note: (Note, status value differs from K15.FR.04). Charging Station will use a TxDefaultProfile or
              provide a schedule with maximum power of EVSE.
System under test   CSMS

Description         Authorization of an EV by the CSMS to start a V2X power transfer loop.

Purpose             To check if the CSMS supports ISO15118-20 Dymanic Control without setting a charging
                    profile.

Prerequisite(s)     CSMS supports ISO15118-20
                    The CSMS is able to turn off providing a Charging Profile during negotiation.

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is ISO15118-20 transaction just started exposing:
                    - <allowedEnergyTransferModes>
                    - <transactionId>

Test Scenario
1. The Test System sends a NotifyEVChargingNeedsRequest with:
    - evseId <Configured evseId>
    - chargingNeeds.requestedEnergyTransfer one of <allowedEnergyTransferModes> or if omitted AC_three_phase
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_two_phase, AC_three_phase, AC_BPT,
      AC_BPT_DER, AC_DER]
    - chargingNeeds.controlMode DynamicControl
    - chargingNeeds.v2xChargingParameters.maxChargePower 8000W
    - chargingNeeds.v2xChargingParameters.maxDischargePower 0W
2. Then CSMS SHALL respond with a NotifyEVChargingNeedsResponse

Tool validations
* Step 2:
    Message: NotifyEVChargingNeedsResponse
    - status must be NoChargingProfile

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
