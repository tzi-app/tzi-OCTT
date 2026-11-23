"""
State               ISO15118SmartCharging
System under test   CSMS
Description         A version for the ISO15118 can be specified as argument to this reusable state. This
                    version is exposed as variable <iso15118Version> and can either be iso15118-2 or
                    iso15118-20. If not specified iso15118-2 will be assumed.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

1. The Test System sends a NotifyEVChargingNeedsRequest with
   evseId <Configured evseId>
   maxScheduleTuples 2
   if <iso15118Version> is iso15118-2:
       chargingNeeds.requestedEnergyTransfer AC_three_phase
       chargingNeeds.acChargingParameters.energyAmount 50000
       chargingNeeds.acChargingParameters.evMinCurrent 0
       chargingNeeds.acChargingParameters.evMaxCurrent 32
       chargingNeeds.acChargingParameters.evMaxVoltage 230
   end if
   if <iso15118Version> is iso15118-20:
       chargingNeeds.requestedEnergyTransfer AC_single_phase
       chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
       chargingNeeds.controlMode ScheduledControl
       chargingNeeds.v2xChargingParameters.maxChargePower 10000
       chargingNeeds.v2xChargingParameters.maxDischargePower 10000
   end if
2. The CSMS responds with a NotifyEVChargingNeedsResponse.
3. The CSMS sends a SetChargingProfileRequest
   Note(s):
   - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
     request
4. The Test System responds with a SetChargingProfileResponse with:
   status Accepted
5. The Test System sends a NotifyEVChargingScheduleRequest with
   evseId <COnfigured evseId>
   chargingSchedule <ChargingSchedule provided at step 3>
6. The CSMS responds with a NotifyEVChargingScheduleResponse.
7. The Test System sends a TransactionEventRequest with
   triggerReason <ChargingStateChanged>
   transactionInfo.chargingState <Charging>
8. The CSMS responds with a TransactionEventResponse.

Tool validations
* Step 2: Message: NotifyEVChargingNeedsResponse - Status must be Accepted or Processing
* Step 3: Message: SetChargingProfileRequest
  - chargingProfilePurpose must be <TxProfile>
  - transactionId must be <Provided transactionId from before>
* Step 4: Message: NotifyEVChargingScheduleResponse - status must be <Accepted>
Post condition      N/a
"""
