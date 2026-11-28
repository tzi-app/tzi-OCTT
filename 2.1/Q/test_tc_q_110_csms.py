"""
Test case name      Central V2X control with dynamic CSMS setpoint - pull
Test case Id        TC_Q_110_CSMS
Use case Id(s)      Q04, K28
Requirement(s)      K28.FR.01, K28.FR.02, K28.FR.07, K28.FR.12

Requirement Details:
    K28.FR.01: A ChargingProfileType with chargingProfileKind = Dynamic SHALL consist of only 1
               ChargingScheduleType with only 1 ChargingSchedulePeriodType
    K28.FR.02: The ChargingSchedulePeriodType in a ChargingProfileType with chargingProfileKind = Dynamic
               SHALL have a startPeriod = 0
        Note: It becomes immediately active upon receipt of the message.
    K28.FR.07: CSMS SHALL respond with PullDynamicScheduleUpdateResponse with status = Accepted and the
               limits/setpoints to use in the charging profile.
        Precondition: When CSMS receives a PullDynamicScheduleUpdateRequest for a charging profile that has
                      chargingProfileKind = Dynamic
    K28.FR.12: CSMS SHALL respond with a status = Rejected and optionally a statusInfo.reasonCode =
               InvalidProfile
        Precondition: When CSMS receives a PullDynamicScheduleUpdateRequest for a charging profile that does
                      not exist or does not have chargingProfileKind = Dynamic
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to support DynamicControl charging profiles and a CS is able
                    to pull from CSMS.

Prerequisite(s)     - CSMS supports Bidirectional Power Transfer

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to send a TxDefaultProfile dynamic charging profile to the CS with
    - dynUpdateInterval 15

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with status Accepted
3. The Test System sends a PullDynamicScheduleUpdateRequest with
    - chargingProfileId <unknown chargingProfileId>
4. The CSMS responds with a PullDynamicScheduleUpdateResponse
5. The Test System sends a PullDynamicScheduleUpdateRequest with
    - chargingProfileId <SetChargingProfileRequest.chargingProfile.id from step 1>
6. The CSMS responds with a PullDynamicScheduleUpdateResponse

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfileKind must be Dynamic
    - chargingProfile.dynUpdateInterval must be 15
    - chargingProfile.dynUpdateTime must be <not omitted>
    - chargingProfile.chargingSchedule must be size = 1
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriods must be size = 1
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].startPeriod must be 0
* Step 4:
    Message: PullDynamicScheduleUpdateResponse
    - status must be Rejected
* Step 6:
    Message: PullDynamicScheduleUpdateResponse
    - status must be Accepted
    - scheduleUpdate must be <not omitted>
    - scheduleUpdate must at least have a single field set

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from smart_charging import charging_profile, request_charging_profile
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])

# A chargingProfileId that the CSMS has not sent: <unknown chargingProfileId>
UNKNOWN_CHARGING_PROFILE_ID = 987654


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_q_110(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to send a TxDefaultProfile dynamic charging profile to the
    #                CS with
    #     - dynUpdateInterval 15
    # 1. The CSMS sends a SetChargingProfileRequest
    # 2. The Test System responds with a SetChargingProfileResponse with status Accepted
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, charging_profile(
        'TxDefaultProfile', 'Dynamic', 16, duration=False, dynUpdateInterval=15,
        dynUpdateTime=utc_now_iso()))
    profile = request.charging_profile
    assert profile.charging_profile_kind == 'Dynamic', \
        f"Expected chargingProfile.chargingProfileKind Dynamic, got {profile.charging_profile_kind}"
    assert profile.dyn_update_interval == 15, \
        f"Expected chargingProfile.dynUpdateInterval 15, got {profile.dyn_update_interval}"
    assert profile.dyn_update_time is not None, "chargingProfile.dynUpdateTime must not be omitted"
    assert len(profile.charging_schedule) == 1, \
        f"chargingProfile.chargingSchedule must be size = 1, got {len(profile.charging_schedule)}"
    periods = profile.charging_schedule[0].charging_schedule_period
    assert len(periods) == 1, \
        f"chargingSchedule[0].chargingSchedulePeriod must be size = 1, got {len(periods)}"
    assert periods[0].start_period == 0, \
        f"Expected chargingSchedule[0].chargingSchedulePeriod[0].startPeriod 0, got {periods[0].start_period}"

    # 3. The Test System sends a PullDynamicScheduleUpdateRequest with
    #    - chargingProfileId <unknown chargingProfileId>
    # 4. The CSMS responds with a PullDynamicScheduleUpdateResponse
    response = await cp.call(call.PullDynamicScheduleUpdate(
        charging_profile_id=UNKNOWN_CHARGING_PROFILE_ID))
    assert response.status == 'Rejected', \
        f"Expected PullDynamicScheduleUpdateResponse.status Rejected, got {response.status}"

    # 5. The Test System sends a PullDynamicScheduleUpdateRequest with
    #    - chargingProfileId <SetChargingProfileRequest.chargingProfile.id from step 1>
    # 6. The CSMS responds with a PullDynamicScheduleUpdateResponse
    response = await cp.call(call.PullDynamicScheduleUpdate(charging_profile_id=profile.id))
    assert response.status == 'Accepted', \
        f"Expected PullDynamicScheduleUpdateResponse.status Accepted, got {response.status}"
    assert response.schedule_update is not None, \
        "PullDynamicScheduleUpdateResponse.scheduleUpdate must not be omitted"
    assert any(value is not None for value in response.schedule_update.values()), \
        "PullDynamicScheduleUpdateResponse.scheduleUpdate must at least have a single field set"

    start_task.cancel()
