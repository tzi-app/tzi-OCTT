"""
Test case name      Set Charging Profile - Multiple Profiles
Test case Id        TC_K_70_CSMS
Use case Id(s)      n/a
Requirement(s)      n/a
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to set multiple Charging Profiles.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a SetChargingProfileRequest with
    - chargingProfilePurpose TxDefaultProfile
2. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
3. The CSMS sends a SetChargingProfileRequest with
    - chargingProfilePurpose ChargingStationMaxProfile
4. The Test System responds with a SetChargingProfileResponse with
    - status Accepted

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose TxDefaultProfile
    - chargingProfile.chargingProfileKind is Absolute OR Recurring
    - chargingProfile.chargingSchedule.startSchedule must NOT be omitted.
    - If chargingProfile.chargingProfileKind is Recurring then chargingProfile.recurrencyKind must NOT be
      omitted.
* Step 3:
    Message SetChargingProfileRequest
    - chargingProfile.id <different id from chargingProfile at step 1>
    - chargingProfile.chargingProfilePurpose ChargingStationMaxProfile
    - chargingProfile.chargingProfileKind is Absolute
    - chargingProfile.chargingSchedule.startSchedule must NOT be omitted.

The received Charging Profiles must comply with the requirements defined at part 2 specification.

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from smart_charging import (
    charging_profile,
    CHARGING_PROFILE_ID,
    only_schedule,
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


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_70(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    await energy_transfer_started(cp)

    # 1. The CSMS sends a SetChargingProfileRequest with
    #    - chargingProfilePurpose TxDefaultProfile
    # 2. The Test System responds with a SetChargingProfileResponse with
    #    - status Accepted
    first = await request_charging_profile(
        cp, CONFIGURED_EVSE_ID, charging_profile('TxDefaultProfile', 'Absolute', 6))
    # chargingProfilePurpose TxDefaultProfile, chargingProfileKind is Absolute OR Recurring
    validate_profile(first, purpose='TxDefaultProfile', kind=('Absolute', 'Recurring'), stack_level=None)
    # chargingSchedule.startSchedule must NOT be omitted
    validate_schedule(only_schedule(first), start_schedule=True, charging_rate_unit=None)
    # If chargingProfileKind is Recurring then recurrencyKind must NOT be omitted.
    validate_recurrency_kind(first.charging_profile)

    # 3. The CSMS sends a SetChargingProfileRequest with
    #    - chargingProfilePurpose ChargingStationMaxProfile
    # 4. The Test System responds with a SetChargingProfileResponse with
    #    - status Accepted
    second = await request_charging_profile(cp, 0, charging_profile(
        'ChargingStationMaxProfile', 'Absolute', 8, profile_id=CHARGING_PROFILE_ID + 1))
    # chargingProfile.id <different id from chargingProfile at step 1>
    assert second.charging_profile.id != first.charging_profile.id, \
        f"The chargingProfile.id of step 3 must be different from the one of step 1: " \
        f"{second.charging_profile.id}"
    # chargingProfilePurpose ChargingStationMaxProfile, chargingProfileKind is Absolute
    validate_profile(second, purpose='ChargingStationMaxProfile', kind='Absolute', stack_level=None)
    # chargingSchedule.startSchedule must NOT be omitted
    validate_schedule(only_schedule(second), start_schedule=True, charging_rate_unit=None)

    # The received Charging Profiles must comply with the requirements defined at part 2
    # specification.
    validate_part_2_requirements(first.charging_profile, evse_id=first.evse_id)
    validate_part_2_requirements(second.charging_profile, evse_id=second.evse_id)

    start_task.cancel()
