"""
State               ISO15118-20 transaction started in V2X AC_BPT energy transfer mode
System under test   CSMS
Description         Starts ISO15118-20 transaction and upgrades to V2X AC_BPT energy transfer mode
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      State is ISO15118-20 transaction just started exposing:
                            - <allowedEnergyTransferModes>
                            - <transactionId>

Main

Agree on energy transfer mode

1. The Test System sends a NotifyEVChargingNeedsRequest with:
   evseId = <Configured evseId>
   chargingNeeds.requestedEnergyTransfer = AC_BPT
   chargingNeeds.availableEnergyTransfer = [AC_single_phase, AC_two_phase, AC_three_phase, AC_BPT, AC_BPT_DER,
   AC_DER]
   chargingNeeds.controlMode = ScheduledControl
   chargingNeeds.v2xChargingParameters.maxChargePower = 1234W
   chargingNeeds.v2xChargingParameters.maxDischargePower = 0W
2. The CSMS responds with a NotifyEVChargingNeedsResponse

Tool validations
* Step 2: Message: NotifyEVChargingNeedsResponse - status must be Accepted or Processing
Post condition      N/a

Remarks
Exposes <allowedEnergyTransferModes>
<transactionId>
"""
