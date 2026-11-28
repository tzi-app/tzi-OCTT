"""
Test case name      Clear Charging Profile - Without previous charging profile
Test case Id        TC_K_08_CSMS
Use case Id(s)      K10
Requirement(s)      N/a
System under test   CSMS

Description         If the CSMS wishes to clear some or all of the charging profiles that were previously sent
                    to the Charging Station, then the CSMS sends a ClearChargingProfileRequest to the Charging
                    Station.

Purpose             To verify if the CSMS is able to request the charging station to clear a specific charging
                    profile with a chargingProfileId and stackLevel/purpose combination while the Charging
                    stations does not accept as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a ClearChargingProfileRequest with
    - chargingProfilePurpose TxDefaultProfile AND
    - evseId <Configured evseId> AND
    - stackLevel <Configured stackLevel>
2. The Test System responds with a ClearChargingProfileResponse with
    - status Unknown

Tool validations
* Step 1:
    Message ClearChargingProfileRequest
    - chargingProfileCriteria.chargingProfilePurpose TxDefaultProfile AND
    - chargingProfileCriteria.stackLevel <Configured stackLevel> AND
    - chargingProfileCriteria.evseId <Configured evseId> AND
    - chargingProfileId must be omitted.

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from smart_charging import STACK_LEVEL
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_08(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a ClearChargingProfileRequest with
    #    - chargingProfilePurpose TxDefaultProfile AND
    #    - evseId <Configured evseId> AND
    #    - stackLevel <Configured stackLevel>
    # 2. The Test System responds with a ClearChargingProfileResponse with
    #    - status Unknown
    cp.set_response('ClearChargingProfile', status='Unknown')
    request = await cp.wait_for_request(
        'ClearChargingProfile',
        manual_action=send_call(BASIC_AUTH_CP, 'ClearChargingProfile', {
            'chargingProfileCriteria': {
                'chargingProfilePurpose': 'TxDefaultProfile',
                'evseId': CONFIGURED_EVSE_ID,
                'stackLevel': STACK_LEVEL,
            },
        }))
    criteria = request.charging_profile_criteria
    assert criteria is not None, "ClearChargingProfileRequest has no chargingProfileCriteria"
    assert criteria.charging_profile_purpose == 'TxDefaultProfile', \
        f"Expected chargingProfileCriteria.chargingProfilePurpose TxDefaultProfile, " \
        f"got {criteria.charging_profile_purpose}"
    assert criteria.stack_level == STACK_LEVEL, \
        f"Expected chargingProfileCriteria.stackLevel {STACK_LEVEL}, got {criteria.stack_level}"
    assert criteria.evse_id == CONFIGURED_EVSE_ID, \
        f"Expected chargingProfileCriteria.evseId {CONFIGURED_EVSE_ID}, got {criteria.evse_id}"
    assert request.charging_profile_id is None, \
        f"ClearChargingProfileRequest.chargingProfileId must be omitted, got {request.charging_profile_id}"

    start_task.cancel()
