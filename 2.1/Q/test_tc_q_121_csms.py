"""
Test case name      Frequency Support - Local V2X control
Test case Id        TC_Q_121_CSMS
Use case Id(s)      Q08
Requirement(s)      Q08.FR.01, Q08.FR.02, Q08.FR.05

Requirement Details:
    Q08.FR.01: The ChargingSchedulePeriodType SHALL NOT contain the fields limit, dischargeLimit, setpoint,
               setpointReactive.
        Precondition: When a ChargingSchedulePeriodType has operationMode = LocalFrequency
        Note: This also applies to the L2 and L3 variants of these fields. The power setpoint is calculated
              from v2xFreqWattCurve and v2xBaseline.
    Q08.FR.02: The ChargingSchedulePeriodType SHALL have a v2xFreqWattCurve with at least two
               V2XFreqWattPointType elements, and a value for v2xBaseline, and optionally a v2xSignalWattCurve
               with at least two V2XSignalWattPointType elements.
        Precondition: Q08.FR.01
    Q08.FR.05: The ChargingScheduleType that contains the ChargingSchedulePeriodType SHALL have
               chargingRateUnit = W.
        Precondition: Q08.FR.01
        Note: A frequency-watt curve specifies power in Watts.
System under test   CSMS

Description         To allow an EV to be used for frequency control, depending on local frequency readings.

Purpose             To check if the CSMS supports Local V2X control for frequency support.

Prerequisite(s)     - CSMS supports Bidirectional Power Transfer
                    - CSMS has Frequency support

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is ISO15118-20 transaction just started exposing:
                    - <allowedEnergyTransferModes>
                    - <transactionId>

Test Scenario
Agree on energy transfer mode

1. The Test System sends a NotifyEVChargingNeedsRequest with
    - evseId = <Configured evseId>
    - chargingNeeds.requestedEnergyTransfer AC_BPT
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_two_phase, AC_three_phase, AC_BPT,
      AC_BPT_DER, AC_DER]
    - chargingNeeds.controlMode DynamicControl
    - chargingNeeds.v2xChargingParameters.maxChargePower 1234W
    - chargingNeeds.v2xChargingParameters.maxDischargePower 4321W
2. The CSMS responds with a NotifyEVChargingNeedsResponse
3. The CSMS sends a SetChargingProfileRequest
4. And Test System responds with a SetChargingProfileResponse with
    - status Accepted

Manual Action: Request the CSMS to send a LocalFrequency charging profile to the CS
    - evseId <Configured evseId>
    - chargingProfile.transactionId <transactionId>
    - chargingProfile.chargingProfilePurpose TxProfile
    - chargingProfile.chargingSchedule.chargingRateUnit W
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.operationMode must be LocalFrequency
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[0].frequency 49.5
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[0].power -1000
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[1].frequency 50.0
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[1].power 0
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[2].frequency 50.5
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[2].power 1000
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xBaseline 7000

5. The CSMS sends a SetChargingProfileRequest
6. And Test System responds with a SetChargingProfileResponse with
    - status Accepted

Tool validations
* Step 2:
    Message: NotifyEVChargingNeedsResponse
    - status must be Accepted or Processing
* Step 5:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfile.transactionId must be <transactionId>
    - chargingProfile.chargingProfilePurpose must be TxProfile
    - chargingProfile.chargingSchedule.chargingRateUnit must be W
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.operationMode must be LocalFrequency
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit_L2 must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit_L3 must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.dischargeLimit must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.dischargeLimit_L2 must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.dischargeLimit_L3 must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpoint must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpoint_L2 must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpoint_L3 must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpointReactive must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpointReactive_L2 must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpointReactive_L3 must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[0].frequency must be <not
      omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[0].power must be <not omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[1].frequency must be <not
      omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[1].power must be <not omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[2].frequency must be <not
      omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xFreqWattCurve[2].power must be <not omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.v2xBaseline must be <not omitted>

Post scenario validations:
    N/a
"""
