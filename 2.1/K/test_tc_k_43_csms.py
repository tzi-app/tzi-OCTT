"""
Test case name      Get Composite Schedule - Specific EVSE
Test case Id        TC_K_43_CSMS
Use case Id(s)      K08
Requirement(s)      K08.FR.01

Requirement Details:
    K08.FR.01: The CSMS MAY request the Charging Station to report the CompositeSchedule by sending
               GetCompositeScheduleRequest.
System under test   CSMS

Description         The CSMS requests a composite schedule which is a combination of local limits and the
                    prevailing Charging Profiles of the different chargingProfilePurposes and stack levels.

Purpose             To verify if the CSMS is able to calculate request a composite schedule from the Charging
                    Station for a specific EVSE.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a GetCompositeScheduleRequest
2. The Test System responds with a GetCompositeScheduleResponse
    - With status Accepted
    - schedule.evseId 1
    - schedule.duration is 300
    - schedule.chargingRateUnit <Specified chargingRateUnit from step 1>
    - schedule.chargingSchedulePeriod[0].startPeriod 0
    Note: Multiply limit by 1000 if chargingRateUnit is W
    - schedule.chargingSchedulePeriod[0].limit 10

Tool validations
* Step 1:
    Message GetCompositeScheduleRequest
    - evseId 1
    - duration is <Configured duration>
    - chargingRateUnit <Configured chargingRateUnit>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from smart_charging import CHARGING_RATE_UNIT, DURATION, limit_of
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_43(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a GetCompositeScheduleRequest
    # 2. The Test System responds with a GetCompositeScheduleResponse
    #    - With status Accepted
    #    - schedule.evseId 1
    #    - schedule.duration is 300
    #    - schedule.chargingRateUnit <Specified chargingRateUnit from step 1>
    #    - schedule.chargingSchedulePeriod[0].startPeriod 0
    #    - schedule.chargingSchedulePeriod[0].limit 10
    #    Note: Multiply limit by 1000 if chargingRateUnit is W
    cp.set_response('GetCompositeSchedule', lambda request: {
        'status': 'Accepted',
        'schedule': {
            'evse_id': 1,
            'duration': 300,
            'schedule_start': utc_now_iso(),
            'charging_rate_unit': request.charging_rate_unit or CHARGING_RATE_UNIT,
            'charging_schedule_period': [{
                'start_period': 0,
                'limit': limit_of(10, request.charging_rate_unit or CHARGING_RATE_UNIT),
            }],
        },
    })
    request = await cp.wait_for_request(
        'GetCompositeSchedule',
        manual_action=send_call(BASIC_AUTH_CP, 'GetCompositeSchedule', {
            'evseId': 1,
            'duration': DURATION,
            'chargingRateUnit': CHARGING_RATE_UNIT,
        }))
    assert request.evse_id == 1, f"Expected GetCompositeScheduleRequest.evseId 1, got {request.evse_id}"
    assert request.duration == DURATION, \
        f"Expected GetCompositeScheduleRequest.duration {DURATION}, got {request.duration}"
    assert request.charging_rate_unit == CHARGING_RATE_UNIT, \
        f"Expected GetCompositeScheduleRequest.chargingRateUnit {CHARGING_RATE_UNIT}, " \
        f"got {request.charging_rate_unit}"

    start_task.cancel()
