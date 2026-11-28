"""
Test case name      Replace charging profile - With chargingProfileId
Test case Id        TC_K_04_CSMS
Use case Id(s)      n/a
Requirement(s)      n/a
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to replace a charging profile with the same ProfileKind,
                    Purpose, and stackLevel, but a different limit.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a SetChargingProfileRequest with
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 8.0 or 8000.0
2. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
3. The CSMS sends a SetChargingProfileRequest with
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 6.0 or 6000.0
4. The Test System responds with a SetChargingProfileResponse with
    - status Accepted

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 8.0 (A) or 8000.0 (W)
    The chargingSchedule contains only one chargingSchedulePeriod
* Step 3:
    Message SetChargingProfileRequest
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 6.0 (A) or 6000.0 (W)
    The chargingSchedule contains only one chargingSchedulePeriod
* Step 1/3:
    Message SetChargingProfileRequest
    - chargingProfile.id <Same id for both chargingProfiles>
    - chargingProfile.chargingSchedule.startSchedule must NOT be omitted.
    - chargingProfile.stackLevel <Configured stackLevel> AND
    - chargingProfile.chargingProfilePurpose <Equal value for both profiles> AND (TxDefaultProfile OR
      ChargingStationMaxProfile)
    - chargingProfile.chargingProfileKind <Equal value for both profiles> AND
    If chargingProfile.chargingProfilePurpose is TxDefaultProfile then chargingProfile.chargingProfileKind
    must be Absolute OR Recurring
    If chargingProfile.chargingProfilePurpose is ChargingStationMaxProfile then
    chargingProfile.chargingProfileKind must be Absolute
    If chargingProfile.chargingProfileKind is Recurring then chargingProfile.recurrencyKind must NOT be
    omitted, else omitted

    The received Charging Profiles must comply with the requirements defined at part 2 specification.

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from smart_charging import (
    charging_profile,
    request_charging_profile,
    validate_part_2_requirements,
    validate_profile,
    validate_recurrency_kind,
    validate_schedule,
)
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


def validate_step(request, amperes):
    """The validations of both SetChargingProfileRequests."""
    profile = request.charging_profile
    # The chargingSchedule contains only one chargingSchedulePeriod, with startPeriod 0 and
    # the limit of the step
    assert len(profile.charging_schedule) == 1, \
        f"Expected one chargingSchedule, got {len(profile.charging_schedule)}"
    schedule = profile.charging_schedule[0]
    assert len(schedule.charging_schedule_period) == 1, \
        f"Expected one chargingSchedulePeriod, got {len(schedule.charging_schedule_period)}"
    # chargingSchedule.startSchedule must NOT be omitted
    validate_schedule(schedule, amperes=amperes, start_schedule=True, charging_rate_unit=None,
                      number_phases=False)
    # stackLevel <Configured stackLevel>, chargingProfilePurpose TxDefaultProfile OR
    # ChargingStationMaxProfile
    validate_profile(request)
    purpose, kind = profile.charging_profile_purpose, profile.charging_profile_kind
    assert purpose in ('TxDefaultProfile', 'ChargingStationMaxProfile'), \
        f"Expected chargingProfilePurpose TxDefaultProfile or ChargingStationMaxProfile, got {purpose}"
    # If chargingProfilePurpose is TxDefaultProfile then chargingProfileKind must be Absolute
    # OR Recurring. If it is ChargingStationMaxProfile then it must be Absolute.
    allowed = ('Absolute', 'Recurring') if purpose == 'TxDefaultProfile' else ('Absolute',)
    assert kind in allowed, \
        f"Expected chargingProfileKind {' or '.join(allowed)} for a {purpose}, got {kind}"
    # If chargingProfileKind is Recurring then recurrencyKind must NOT be omitted, else omitted
    validate_recurrency_kind(profile)
    # The received Charging Profiles must comply with the requirements defined at part 2
    # specification.
    validate_part_2_requirements(profile, evse_id=request.evse_id)


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_04(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a SetChargingProfileRequest with
    #    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 8.0 or 8000.0
    # 2. The Test System responds with a SetChargingProfileResponse with status Accepted
    first = await request_charging_profile(
        cp, CONFIGURED_EVSE_ID, charging_profile('TxDefaultProfile', 'Absolute', 8))
    validate_step(first, amperes=8)

    # 3. The CSMS sends a SetChargingProfileRequest with
    #    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 6.0 or 6000.0
    # 4. The Test System responds with a SetChargingProfileResponse with status Accepted
    second = await request_charging_profile(
        cp, CONFIGURED_EVSE_ID, charging_profile('TxDefaultProfile', 'Absolute', 6))
    validate_step(second, amperes=6)

    # Step 1/3: chargingProfile.id <Same id for both chargingProfiles>, chargingProfilePurpose
    # and chargingProfileKind <Equal value for both profiles>
    assert second.charging_profile.id == first.charging_profile.id, \
        f"Expected the same chargingProfile.id in both requests, got {first.charging_profile.id} " \
        f"and {second.charging_profile.id}"
    purposes = [request.charging_profile.charging_profile_purpose for request in (first, second)]
    assert purposes[0] == purposes[1], \
        f"Expected the same chargingProfilePurpose in both requests, got {purposes}"
    kinds = [request.charging_profile.charging_profile_kind for request in (first, second)]
    assert kinds[0] == kinds[1], f"Expected the same chargingProfileKind in both requests, got {kinds}"

    start_task.cancel()
