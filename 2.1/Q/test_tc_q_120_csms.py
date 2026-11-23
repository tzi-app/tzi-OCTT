"""
Test case name      Frequency Support - Local V2X control - AFRR support
Test case Id        TC_Q_120_CSMS
Use case Id(s)      Q08
Requirement(s)      Q08.FR.01, Q08.FR.02, Q08.FR.05, Q08.FR.12

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
    Q08.FR.12: CSMS SHALL send a AFRRSignalRequest with timestamp set to current time and signal set to value
               received from external actor.
        Precondition: When CSMS receives an aFRR signal from an external actor
        Note: External actor is, for example, a TSO.
System under test   CSMS

Description         To allow an EV to be used for aFRR frequency control, depending on a aFRR signal request
                    that CSMS receives from an external actor.

Purpose             To verify if the CSMS is able to produce a charging profile for aFRR frequency support.

Prerequisite(s)     - CSMS supports Bidirectional Power Transfer
                    - CSMS has Frequency support

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual action: trigger CSMS to set a TxDefaultProfile Charging Profile with chargingSchedulePeriod with
               operationMode LocalFrequency and v2xBaseline
and v2xFreqWattCurve
and v2xSignalWattCurve.

1. The CSMS the sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with
    - status Accepted

Manual action: trigger CSMS to send out a AFRRSignalRequest with a given value for signal

3. The CSMS sends a AFRRSignalRequest
4. The Test System responds with a AFRRSignalResponse with
    - status Accepted

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose must be TxDefaultProfile
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].operationMode must be LocalFrequency
    - chargingProfile.chargingSchedule[0].chargingRateUnit must be W
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].limit must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].limit_L2 must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].limit_L3 must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].dischargeLimit must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].dischargeLimit_L2 must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].dischargeLimit_L3 must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpoint must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpoint_L2 must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpoint_L3 must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpointReactive must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpointReactive_L2 must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpointReactive_L3 must be <omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].v2xBaseline must be <not omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].v2xFreqWattCurve size must be >= 2
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].v2xFreqWattCurve[*].frequency must be <not
      omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].v2xFreqWattCurve[*].power must be <not
      omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].v2xSignalWattCurve size must be >= 2
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].v2xSignalWattCurve[*].signal must be <not
      omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].v2xSignalWattCurve[*].power must be <not
      omitted>
* Step 3:
    Message: AFRRSignalRequest
    - signal must <be the value that was provided in manual action before step 3.>

Post scenario validations:
    N/a
"""
