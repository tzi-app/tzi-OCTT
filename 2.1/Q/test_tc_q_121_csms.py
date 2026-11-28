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

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.iso15118_20_transaction_just_started import (
    iso15118_20_transaction_just_started,
    V2X_VARIABLES,
)
from reusable_states.iso15118_smart_charging import negotiate_charging_schedule, validate_tx_profile
from smart_charging import only_schedule, POWER_FIELDS, request_charging_profile, v2x_profile
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_q_121(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # The Test System supports ISO 15118-20 and V2X.
    cp.variables = dict(V2X_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is ISO15118-20 transaction just started exposing
    #                 <allowedEnergyTransferModes> and <transactionId>
    _, transaction_id = await iso15118_20_transaction_just_started(cp)

    # Agree on energy transfer mode
    # 1. The Test System sends a NotifyEVChargingNeedsRequest with
    #    - evseId = <Configured evseId>
    #    - chargingNeeds.requestedEnergyTransfer AC_BPT
    #    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_two_phase, AC_three_phase,
    #      AC_BPT, AC_BPT_DER, AC_DER]
    #    - chargingNeeds.controlMode DynamicControl
    #    - chargingNeeds.v2xChargingParameters.maxChargePower 1234W
    #    - chargingNeeds.v2xChargingParameters.maxDischargePower 4321W
    # 2. The CSMS responds with a NotifyEVChargingNeedsResponse
    #    - status must be Accepted or Processing
    # 3. The CSMS sends a SetChargingProfileRequest
    # 4. And Test System responds with a SetChargingProfileResponse with
    #    - status Accepted
    first = await negotiate_charging_schedule(cp, {
        'requested_energy_transfer': 'AC_BPT',
        'available_energy_transfer': ['AC_single_phase', 'AC_two_phase', 'AC_three_phase', 'AC_BPT',
                                      'AC_BPT_DER', 'AC_DER'],
        'control_mode': 'DynamicControl',
        'v2x_charging_parameters': {'max_charge_power': 1234, 'max_discharge_power': 4321},
    }, max_schedule_tuples=None, validate=False)

    # Manual Action: Request the CSMS to send a LocalFrequency charging profile to the CS
    #     - evseId <Configured evseId>
    #     - chargingProfile.transactionId <transactionId>
    #     - chargingProfile.chargingProfilePurpose TxProfile
    #     - chargingProfile.chargingSchedule.chargingRateUnit W
    #     - chargingSchedulePeriod.operationMode must be LocalFrequency
    #     - chargingSchedulePeriod.v2xFreqWattCurve[0]: frequency 49.5, power -1000
    #     - chargingSchedulePeriod.v2xFreqWattCurve[1]: frequency 50.0, power 0
    #     - chargingSchedulePeriod.v2xFreqWattCurve[2]: frequency 50.5, power 1000
    #     - chargingSchedulePeriod.v2xBaseline 7000
    # 5. The CSMS sends a SetChargingProfileRequest
    # 6. And Test System responds with a SetChargingProfileResponse with
    #    - status Accepted
    # The new TxProfile replaces the one of step 3: it has its id (K01.FR.05, K01.FR.39).
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, v2x_profile(
        'TxProfile', 'Absolute', {
            'operationMode': 'LocalFrequency',
            'v2xFreqWattCurve': [{'frequency': 49.5, 'power': -1000}, {'frequency': 50.0, 'power': 0},
                                 {'frequency': 50.5, 'power': 1000}],
            'v2xBaseline': 7000,
        }, profile_id=first.charging_profile.id, transactionId=transaction_id))
    # evseId <Configured evseId>, chargingProfile.transactionId <transactionId>,
    # chargingProfilePurpose TxProfile
    validate_tx_profile(request, transaction_id)
    schedule = only_schedule(request)
    assert schedule.charging_rate_unit == 'W', \
        f"Expected chargingSchedule.chargingRateUnit W, got {schedule.charging_rate_unit}"
    period = schedule.charging_schedule_period[0]
    assert period.operation_mode == 'LocalFrequency', \
        f"Expected chargingSchedulePeriod.operationMode LocalFrequency, got {period.operation_mode}"
    # The limits, discharge limits, setpoints and reactive setpoints must be <omitted>
    for name in POWER_FIELDS:
        assert period[name] is None, f"chargingSchedulePeriod.{name} must be omitted, got {period[name]}"
    curve = period.v2x_freq_watt_curve
    assert curve is not None and len(curve) >= 3, \
        f"Expected three points in chargingSchedulePeriod.v2xFreqWattCurve, got {curve}"
    assert all(point.frequency is not None and point.power is not None for point in curve[:3]), \
        f"v2xFreqWattCurve[0..2].frequency and .power must not be omitted: {curve}"
    assert period.v2x_baseline is not None, "chargingSchedulePeriod.v2xBaseline must not be omitted"

    start_task.cancel()
