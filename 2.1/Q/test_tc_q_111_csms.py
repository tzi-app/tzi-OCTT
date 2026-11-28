"""
Test case name      External V2X control - with a charging profile from CSMS - setpoint
Test case Id        TC_Q_111_CSMS
Use case Id(s)      Q05
Requirement(s)      …
System under test   CSMS

Description         CSMS explicitly allows an External System to control the charge and discharge behaviour of
                    an EV for a certain period of time.

Purpose             To verify if the CSMS is able to configure the CS to use an External V2X setpoint with
                    relative or dynamic charging profile.

Prerequisite(s)     - CSMS supports Bidirectional Power Transfer

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual action: trigger CSMS to set a TxDefaultProfile, Relative Charging Profile with chargingSchedulePeriod
               with operationMode ExternalSetpoint

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with status Accepted

Manual action: trigger CSMS to set a TxDefaultProfile, Dynamic Charging Profile with chargingSchedulePeriod
               with operationMode ExternalSetpoint

3. The CSMS sends a SetChargingProfileRequest
4. The Test System responds with a SetChargingProfileResponse with status Accepted

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfile.chargingProfilePurpose must be TxDefaultProfile
    - chargingProfile.chargingProfileKind Relative
    - chargingProfile.dynUpdateTime must be <omitted>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].operationMode must be ExternalSetpoint
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setpoint must be <not omitted>
* Step 3:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfile.chargingProfilePurpose must be TxDefaultProfile
    - chargingProfile.chargingProfileKind Dynamic
    - chargingProfile.dynUpdateTime must be <Datetime of moment of step 3>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].operationMode must be ExternalSetpoint
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setpoint must be <not omitted>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod size must be 1
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].startPeriod must be 0

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from authorization import is_current_date_time
from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from smart_charging import (
    request_charging_profile,
    v2x_profile,
    validate_periods,
    validate_profile,
)
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_q_111(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual action: trigger CSMS to set a TxDefaultProfile, Relative Charging Profile with
    #                chargingSchedulePeriod with operationMode ExternalSetpoint
    # 1. The CSMS sends a SetChargingProfileRequest
    # 2. The Test System responds with a SetChargingProfileResponse with status Accepted
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, v2x_profile(
        'TxDefaultProfile', 'Relative', {'operationMode': 'ExternalSetpoint', 'setpoint': 5000}))
    validate_profile(request, evse_id=CONFIGURED_EVSE_ID, purpose='TxDefaultProfile', kind='Relative',
                     stack_level=None)
    assert request.charging_profile.dyn_update_time is None, \
        f"chargingProfile.dynUpdateTime must be omitted, got {request.charging_profile.dyn_update_time}"
    validate_periods(request, operation_mode='ExternalSetpoint', present=('setpoint',))

    # Manual action: trigger CSMS to set a TxDefaultProfile, Dynamic Charging Profile with
    #                chargingSchedulePeriod with operationMode ExternalSetpoint
    # 3. The CSMS sends a SetChargingProfileRequest
    # 4. The Test System responds with a SetChargingProfileResponse with status Accepted
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, v2x_profile(
        'TxDefaultProfile', 'Dynamic', {'operationMode': 'ExternalSetpoint', 'setpoint': 5000},
        dynUpdateTime=utc_now_iso()))
    validate_profile(request, evse_id=CONFIGURED_EVSE_ID, purpose='TxDefaultProfile', kind='Dynamic',
                     stack_level=None)
    # dynUpdateTime must be <Datetime of moment of step 3>
    dyn_update_time = request.charging_profile.dyn_update_time
    assert dyn_update_time is not None and is_current_date_time(dyn_update_time), \
        f"Expected chargingProfile.dynUpdateTime to be the moment of this request, got {dyn_update_time}"
    validate_periods(request, operation_mode='ExternalSetpoint', present=('setpoint',))
    periods = request.charging_profile.charging_schedule[0].charging_schedule_period
    assert len(periods) == 1, f"chargingSchedule[0].chargingSchedulePeriod size must be 1, got {len(periods)}"
    assert periods[0].start_period == 0, \
        f"Expected chargingSchedule[0].chargingSchedulePeriod[0].startPeriod 0, got {periods[0].start_period}"

    start_task.cancel()
