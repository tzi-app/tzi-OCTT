"""
Test case name      Frequency Support - Central V2X control - push
Test case Id        TC_Q_117_CSMS
Use case Id(s)      Q07, Q04, K28
Requirement(s)      K28.FR.01, K28.FR.02

Requirement Details:
    K28.FR.01: A ChargingProfileType with chargingProfileKind = Dynamic SHALL consist of only 1
               ChargingScheduleType with only 1 ChargingSchedulePeriodType
    K28.FR.02: The ChargingSchedulePeriodType in a ChargingProfileType with chargingProfileKind = Dynamic
               SHALL have a startPeriod = 0
        Note: It becomes immediately active upon receipt of the message.
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to support DynamicControl charging profiles and push changes
                    to the CS.

Prerequisite(s)     - CSMS supports Bidirectional Power Transfer

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to send a TxDefaultProfile dynamic charging profile to the CS and update the
               schedule every 15 seconds with
    - operationMode CentralFrequency
    - setpoint -6 * <limit multiplier>
    Note: Check [csms_csKSmartChargingChargingProfileLimits] for <limit multiplier>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with status Accepted
3. The CSMS sends a UpdateDynamicScheduleRequest
4. The Test System responds with a UpdateDynamicScheduleResponse with status Accepted

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfileKind must be Dynamic
    - chargingProfile. must be TxDefaultProfile
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriods must be size 1
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].startPeriod must be 0
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpoint must be -6 * <limit multiplier>
    Note: Check [csms_csKSmartChargingChargingProfileLimits] for <limit multiplier>
* Step 3:
    Message: UpdateDynamicScheduleRequest
    - chargingProfileId must be <SetChargingProfileRequest.chargingProfile.id from step 1>
    - scheduleUpdate.limit must be <not omitted>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import ACTION_TIMEOUT, TziChargePoint21
from reusable_states.booted import booted
from smart_charging import (
    CHARGING_RATE_UNIT,
    limit_of,
    request_charging_profile,
    v2x_profile,
    validate_profile,
)
from trigger import update_dynamic_schedule
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])

# The CSMS updates the schedule every 15 seconds
UPDATE_INTERVAL = 15


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_q_117(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to send a TxDefaultProfile dynamic charging profile to the
    #                CS and update the schedule every 15 seconds with
    #     - operationMode CentralFrequency
    #     - setpoint -6 * <limit multiplier>
    # 1. The CSMS sends a SetChargingProfileRequest
    # 2. The Test System responds with a SetChargingProfileResponse with status Accepted
    setpoint = -limit_of(6)
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, v2x_profile(
        'TxDefaultProfile', 'Dynamic', {'operationMode': 'CentralFrequency', 'setpoint': setpoint},
        charging_rate_unit=CHARGING_RATE_UNIT))
    validate_profile(request, purpose='TxDefaultProfile', kind='Dynamic', stack_level=None)
    schedule = request.charging_profile.charging_schedule[0]
    periods = schedule.charging_schedule_period
    assert len(periods) == 1, f"chargingSchedule[0].chargingSchedulePeriod must be size 1, got {len(periods)}"
    assert periods[0].start_period == 0, \
        f"Expected chargingSchedulePeriod[0].startPeriod 0, got {periods[0].start_period}"
    # setpoint must be -6 * <limit multiplier>: -6 in A, -6000 in W
    assert periods[0].setpoint == -limit_of(6, schedule.charging_rate_unit), \
        f"Expected chargingSchedulePeriod[0].setpoint {-limit_of(6, schedule.charging_rate_unit)}, " \
        f"got {periods[0].setpoint}"
    profile_id = request.charging_profile.id

    # The CSMS updates the schedule every 15 seconds.
    cp.set_response('UpdateDynamicSchedule', status='Accepted')
    cp.forget_requests('UpdateDynamicSchedule')
    await update_dynamic_schedule(BASIC_AUTH_CP, profile_id, UPDATE_INTERVAL,
                                  {'limit': limit_of(6), 'setpoint': setpoint})

    # 3. The CSMS sends a UpdateDynamicScheduleRequest
    # 4. The Test System responds with a UpdateDynamicScheduleResponse with status Accepted
    update = await cp.wait_for_request('UpdateDynamicSchedule', timeout=UPDATE_INTERVAL + ACTION_TIMEOUT)
    assert update.charging_profile_id == profile_id, \
        f"Expected UpdateDynamicScheduleRequest.chargingProfileId {profile_id}, " \
        f"got {update.charging_profile_id}"
    assert update.schedule_update.limit is not None, \
        "UpdateDynamicScheduleRequest.scheduleUpdate.limit must not be omitted"

    start_task.cancel()
