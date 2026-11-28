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

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from smart_charging import (
    POWER_FIELDS,
    request_charging_profile,
    v2x_profile,
    validate_profile,
)
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])

# The value of the aFRR signal of the Manual Action
AFRR_SIGNAL = 250


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_q_120(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual action: trigger CSMS to set a TxDefaultProfile Charging Profile with
    #                chargingSchedulePeriod with operationMode LocalFrequency and v2xBaseline and
    #                v2xFreqWattCurve and v2xSignalWattCurve.
    # 1. The CSMS the sends a SetChargingProfileRequest
    # 2. The Test System responds with a SetChargingProfileResponse with
    #    - status Accepted
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, v2x_profile(
        'TxDefaultProfile', 'Absolute', {
            'operationMode': 'LocalFrequency',
            'v2xBaseline': 0,
            'v2xFreqWattCurve': [{'frequency': 49.5, 'power': -1000}, {'frequency': 50.0, 'power': 0},
                                 {'frequency': 50.5, 'power': 1000}],
            'v2xSignalWattCurve': [{'signal': -1000, 'power': -3000}, {'signal': 0, 'power': 0},
                                   {'signal': 1000, 'power': 3000}],
        }))
    validate_profile(request, purpose='TxDefaultProfile', stack_level=None)
    schedule = request.charging_profile.charging_schedule[0]
    assert schedule.charging_rate_unit == 'W', \
        f"Expected chargingSchedule[0].chargingRateUnit W, got {schedule.charging_rate_unit}"
    period = schedule.charging_schedule_period[0]
    assert period.operation_mode == 'LocalFrequency', \
        f"Expected chargingSchedulePeriod[0].operationMode LocalFrequency, got {period.operation_mode}"
    # The limits, discharge limits, setpoints and reactive setpoints must be <omitted>
    for name in POWER_FIELDS:
        assert period[name] is None, f"chargingSchedulePeriod[0].{name} must be omitted, got {period[name]}"
    assert period.v2x_baseline is not None, "chargingSchedulePeriod[0].v2xBaseline must not be omitted"
    # v2xFreqWattCurve size must be >= 2, with frequency and power; v2xSignalWattCurve size must be
    # >= 2, with signal and power
    assert period.v2x_freq_watt_curve is not None and len(period.v2x_freq_watt_curve) >= 2, \
        f"chargingSchedulePeriod[0].v2xFreqWattCurve size must be >= 2, got {period.v2x_freq_watt_curve}"
    assert all(point.frequency is not None and point.power is not None
               for point in period.v2x_freq_watt_curve), \
        f"v2xFreqWattCurve[*].frequency and .power must not be omitted: {period.v2x_freq_watt_curve}"
    assert period.v2x_signal_watt_curve is not None and len(period.v2x_signal_watt_curve) >= 2, \
        f"chargingSchedulePeriod[0].v2xSignalWattCurve size must be >= 2, got {period.v2x_signal_watt_curve}"
    assert all(point.signal is not None and point.power is not None
               for point in period.v2x_signal_watt_curve), \
        f"v2xSignalWattCurve[*].signal and .power must not be omitted: {period.v2x_signal_watt_curve}"

    # Manual action: trigger CSMS to send out a AFRRSignalRequest with a given value for signal
    # 3. The CSMS sends a AFRRSignalRequest
    # 4. The Test System responds with a AFRRSignalResponse with
    #    - status Accepted
    cp.set_response('AFRRSignal', status='Accepted')
    signal = await cp.wait_for_request(
        'AFRRSignal',
        manual_action=send_call(BASIC_AUTH_CP, 'AFRRSignal',
                                {'timestamp': utc_now_iso(), 'signal': AFRR_SIGNAL}))
    assert signal.signal == AFRR_SIGNAL, \
        f"Expected AFRRSignalRequest.signal {AFRR_SIGNAL} (the value of the Manual Action), " \
        f"got {signal.signal}"

    start_task.cancel()
