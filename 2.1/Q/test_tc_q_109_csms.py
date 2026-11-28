"""
Test case name      Central V2X control with dynamic CSMS setpoint - push
Test case Id        TC_Q_109_CSMS
Use case Id(s)      Q04, K28
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
                    SetChargingProfileRequest to the Charging Station to specify the power or current drawn by
                    EV.

Purpose             To verify if the CSMS is able to support DynamicControl charging profiles and push changes
                    to the CS.

Prerequisite(s)     - CSMS supports Bidirectional Power Transfer

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to send a TxDefaultProfile dynamic charging profile to the CS which will be
               periodically updated every <Configured dynamic profile update interval> seconds by CSMS with
               limit 6 * <limit multiplier>
Note: Check [csms_csKSmartChargingChargingProfileLimits] for <limit multiplier>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
3. The CSMS sends a UpdateDynamicScheduleRequest
4. The Test System responds with a UpdateDynamicScheduleResponse with
    - status Accepted
5. The CSMS sends a UpdateDynamicScheduleRequest
6. The Test System responds with a UpdateDynamicScheduleResponse with
    - status Accepted

Manual Action: Trigger the CSMS to clear the chargingProfile from step 1.

7. The CSMS sends a ClearChargingProfileRequest
8. The Test System responds with a ClearChargingProfileResponse with
    - status Accepted

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfileKind must be Dynamic
    - chargingProfile. must be TxDefaultProfile
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriods must be size 1
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].startPeriod must be 0
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].limit must be 6 * <limit multiplier>
    Note: Check [csms_csKSmartChargingChargingProfileLimits] for <limit multiplier>
* Step 3:
    Message: UpdateDynamicScheduleRequest
    - chargingProfileId must be <SetChargingProfileRequest.chargingProfile.id from step 1>
    - scheduleUpdate.limit must be <not omitted>
* Step 5:
    Message: UpdateDynamicScheduleRequest
    - chargingProfileId must be <SetChargingProfileRequest.chargingProfile.id from step 1>
    - scheduleUpdate.limit must be <not omitted>
* Step 7:
    Message: ClearChargingProfileRequest
    - chargingProfileId <chargingProfileId from step 1 chargingProfile>
    - chargingProfileCriteria omit

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import ACTION_TIMEOUT, TziChargePoint21
from reusable_states.booted import booted
from smart_charging import (
    charging_profile,
    limit_of,
    request_charging_profile,
    validate_profile,
)
from trigger import send_call, update_dynamic_schedule
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
# <Configured dynamic profile update interval>, in seconds
UPDATE_INTERVAL = int(os.environ['CONFIGURED_DYNAMIC_PROFILE_UPDATE_INTERVAL'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_q_109(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to send a TxDefaultProfile dynamic charging profile to the
    #                CS which will be periodically updated every <Configured dynamic profile
    #                update interval> seconds by CSMS with limit 6 * <limit multiplier>
    # 1. The CSMS sends a SetChargingProfileRequest
    # 2. The Test System responds with a SetChargingProfileResponse with
    #    - status Accepted
    request = await request_charging_profile(
        cp, CONFIGURED_EVSE_ID, charging_profile('TxDefaultProfile', 'Dynamic', 6, duration=False))
    validate_profile(request, purpose='TxDefaultProfile', kind='Dynamic', stack_level=None)
    schedule = request.charging_profile.charging_schedule[0]
    periods = schedule.charging_schedule_period
    assert len(periods) == 1, f"chargingSchedule[0].chargingSchedulePeriod must be size 1, got {len(periods)}"
    assert periods[0].start_period == 0, \
        f"Expected chargingSchedulePeriod[0].startPeriod 0, got {periods[0].start_period}"
    # limit must be 6 * <limit multiplier>: 6 in A, 6000 in W
    assert periods[0].limit == limit_of(6, schedule.charging_rate_unit), \
        f"Expected chargingSchedulePeriod[0].limit {limit_of(6, schedule.charging_rate_unit)}, " \
        f"got {periods[0].limit}"
    profile_id = request.charging_profile.id

    # The CSMS updates the charging profile every <Configured dynamic profile update interval>
    # seconds.
    cp.set_response('UpdateDynamicSchedule', status='Accepted')
    cp.forget_requests('UpdateDynamicSchedule')
    await update_dynamic_schedule(BASIC_AUTH_CP, profile_id, UPDATE_INTERVAL, {'limit': limit_of(6)})

    # 3. The CSMS sends a UpdateDynamicScheduleRequest
    # 4. The Test System responds with a UpdateDynamicScheduleResponse with
    #    - status Accepted
    # 5. The CSMS sends a UpdateDynamicScheduleRequest
    # 6. The Test System responds with a UpdateDynamicScheduleResponse with
    #    - status Accepted
    for _ in range(2):
        update = await cp.wait_for_request(
            'UpdateDynamicSchedule', timeout=UPDATE_INTERVAL + ACTION_TIMEOUT)
        assert update.charging_profile_id == profile_id, \
            f"Expected UpdateDynamicScheduleRequest.chargingProfileId {profile_id}, " \
            f"got {update.charging_profile_id}"
        assert update.schedule_update.limit is not None, \
            "UpdateDynamicScheduleRequest.scheduleUpdate.limit must not be omitted"

    # Manual Action: Trigger the CSMS to clear the chargingProfile from step 1.
    # 7. The CSMS sends a ClearChargingProfileRequest
    # 8. The Test System responds with a ClearChargingProfileResponse with
    #    - status Accepted
    cp.set_response('ClearChargingProfile', status='Accepted')
    clear = await cp.wait_for_request(
        'ClearChargingProfile',
        manual_action=send_call(BASIC_AUTH_CP, 'ClearChargingProfile', {'chargingProfileId': profile_id}))
    assert clear.charging_profile_id == profile_id, \
        f"Expected ClearChargingProfileRequest.chargingProfileId {profile_id}, " \
        f"got {clear.charging_profile_id}"
    assert clear.charging_profile_criteria is None, \
        f"ClearChargingProfileRequest.chargingProfileCriteria must be omitted, " \
        f"got {clear.charging_profile_criteria}"

    start_task.cancel()
