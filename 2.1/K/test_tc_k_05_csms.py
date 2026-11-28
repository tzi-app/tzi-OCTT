"""
Test case name      Clear Charging Profile - With chargingProfileId
Test case Id        TC_K_05_CSMS
Use case Id(s)      K10
Requirement(s)      K10.FR.02

Requirement Details:
    K10.FR.02: The CSMS SHALL either specify a chargingProfile.id OR include one or more of the fields
               stackLevel, evseId and chargingProfilePurpose in the ClearChargingProfileRequest to specify
               which Charging Profiles need to be cleared.
System under test   CSMS

Description         If the CSMS wishes to clear some or all of the charging profiles that were previously sent
                    to the Charging Station, then the CSMS sends a ClearChargingProfileRequest to the Charging
                    Station.

Purpose             To verify if the CSMS is able to request the charging station to clear a specific charging
                    profile (not TxDefault) with only a chargingProfileId as described at the OCPP
                    specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        CSMS sends a GetChargingProfilesRequest
                    Test System responds with a GetChargingProfilesResponse with status Accepted
                    Test System sends a ReportChargingProfilesRequest
                    CSMS responds with a ReportChargingProfilesResponse

Reusable State      N/a

Test Scenario
1. The CSMS sends a ClearChargingProfileRequest with
    - chargingProfileId <Generated chargingProfileId> AND
    - chargingProfileCriteria omit
2. The Test System responds with a ClearChargingProfileResponse with status Accepted

Tool validations
* Step 1:
    Message ClearChargingProfileRequest
    - chargingProfileId <Generated chargingProfileId> AND
    - chargingProfileCriteria omit

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from smart_charging import CHARGING_LIMIT_SOURCE, reported_profile
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])

# The id of the charging profile that the Test System has: <Generated chargingProfileId>
GENERATED_CHARGING_PROFILE_ID = 5005


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_05(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Memory State: CSMS sends a GetChargingProfilesRequest
    # The Test System reports its charging profile, so that the CSMS knows the chargingProfileId.
    cp.set_response('GetChargingProfiles', status='Accepted')
    get_profiles = await cp.wait_for_request(
        'GetChargingProfiles',
        manual_action=send_call(BASIC_AUTH_CP, 'GetChargingProfiles', {
            'requestId': 1,
            'evseId': CONFIGURED_EVSE_ID,
            'chargingProfile': {'chargingProfilePurpose': 'TxDefaultProfile'},
        }))
    await cp.call(call.ReportChargingProfiles(
        request_id=get_profiles.request_id,
        charging_limit_source=CHARGING_LIMIT_SOURCE,
        evse_id=CONFIGURED_EVSE_ID,
        charging_profile=[reported_profile(GENERATED_CHARGING_PROFILE_ID, purpose='TxDefaultProfile')],
    ))

    # 1. The CSMS sends a ClearChargingProfileRequest with
    #    - chargingProfileId <Generated chargingProfileId> AND
    #    - chargingProfileCriteria omit
    # 2. The Test System responds with a ClearChargingProfileResponse with status Accepted
    cp.set_response('ClearChargingProfile', status='Accepted')
    request = await cp.wait_for_request(
        'ClearChargingProfile',
        manual_action=send_call(BASIC_AUTH_CP, 'ClearChargingProfile',
                                {'chargingProfileId': GENERATED_CHARGING_PROFILE_ID}))
    assert request.charging_profile_id == GENERATED_CHARGING_PROFILE_ID, \
        f"Expected ClearChargingProfileRequest.chargingProfileId {GENERATED_CHARGING_PROFILE_ID}, " \
        f"got {request.charging_profile_id}"
    assert request.charging_profile_criteria is None, \
        f"ClearChargingProfileRequest.chargingProfileCriteria must be omitted, " \
        f"got {request.charging_profile_criteria}"

    start_task.cancel()
