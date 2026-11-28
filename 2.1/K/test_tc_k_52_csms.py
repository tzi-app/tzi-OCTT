"""
Test case name      EMS Control - Set / Update External Charging Limit (not on a transaction) -
                    ChargingStationExternalConstraints in report
Test case Id        TC_K_52_CSMS
Use case Id(s)      K12
Requirement(s)      N/a
System under test   CSMS

Description         A charging schedule or charging limit can be removed by an external system on the Charging
                    Station. An external control system sends a signal to release a previously imposed
                    charging limit to a Charging Station. The Charging Station notifies the CSMS about this.

Purpose             To verify if the CSMS is able to correctly receive the report when a charging limit has
                    been externally changed in a charging station as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetChargingProfilesRequest
2. The Test System responds with a GetChargingProfilesResponse with
    - status Accepted
3. The Test System sends a ReportChargingProfilesRequest with
    - requestId Generated Id
    - chargingProfile.chargingProfilePurpose ChargingStationExternalConstraints
4. The CSMS responds with a ReportChargingProfilesResponse

Tool validations
N/a

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from smart_charging import reported_profile, request_charging_profiles_report
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_52(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a GetChargingProfilesRequest
    # 2. The Test System responds with a GetChargingProfilesResponse with
    #    - status Accepted
    request = await request_charging_profiles_report(
        cp, evse_id=0, chargingProfilePurpose='ChargingStationExternalConstraints')

    # 3. The Test System sends a ReportChargingProfilesRequest with
    #    - requestId Generated Id
    #    - chargingProfile.chargingProfilePurpose ChargingStationExternalConstraints
    #    The limit comes from an Energy Management System: the chargingLimitSource is EMS.
    # 4. The CSMS responds with a ReportChargingProfilesResponse
    await cp.call(call.ReportChargingProfiles(
        request_id=request.request_id,
        charging_limit_source='EMS',
        evse_id=0,
        charging_profile=[reported_profile(purpose='ChargingStationExternalConstraints')],
    ))

    start_task.cancel()
