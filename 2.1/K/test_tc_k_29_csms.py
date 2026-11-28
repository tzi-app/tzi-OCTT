"""
Test case name      Get Charging Profile - EvseId 0
Test case Id        TC_K_29_CSMS
Use case Id(s)      K09
Requirement(s)      K09.FR.03

Requirement Details:
    K09.FR.03: The CSMS SHALL specify in chargingProfile criteria in GetChargingProfilesRequest either:
               - a (list of) chargingProfileId(s) OR
               - one or more of the fields stackLevel, chargingLimitSource, chargingProfilePurpose.
        Note: These fields are filter values of equal importance, but because a chargingProfileId uniquely
              identifies a charging profile, the other fields are not needed if chargingProfileIds are used.
System under test   CSMS

Description         With the GetChargingProfilesRequest message the CSMS can ask a Charging Station to report
                    all, or a subset of all the install Charging Profiles from the different possible sources.
                    This can be used for some automatic smart charging control system, or for debug purposes
                    by a CSO.

Purpose             To verify if the CSMS is able to request charging profiles installed on the charging
                    station itself and read in the reports as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      EnergyTransferStarted

Test Scenario
1. The CSMS sends a GetChargingProfilesRequest with
    - evseId 0
2. The Test System responds with a GetChargingProfilesResponse with
    - status Accepted
3. The Test System sends a ReportChargingProfilesRequest with
    - requestId <Received requestId>
4. The CSMS responds with a ReportChargingProfilesResponse

Tool validations
* Step 1:
    Message GetChargingProfilesRequest
    - evseId 0 AND
    - chargingProfile.chargingProfilePurpose <Configured chargingProfilePurpose> AND
    Note: chargingProfilePurpose is included, because the chargingProfile field is required and may not be
          left empty.
    - chargingProfile.stackLevel must be omitted AND
    - chargingProfile.chargingLimitSource must be omitted AND
    - chargingProfile.chargingProfileId must be omitted

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] -
        2.16.5. Page 366 - Get Charging Profile
        (Part 2 errata - applies to this test via use case K09)
        The note of K09.FR.05 did not mention LocalGeneration as a possible charging profile purpose on EVSE
        #0. It has been added for consistency.

        Update note

        | ID | Precondition | Requirements | Note |
        | K09.FR.05 | If evseId is set to 0 in GetChargingProfilesRequest | The Charging Station SHALL only
          report charging profiles installed on the Charging Station itself (the grid connection) that match
          all fields in chargingProfile. | EVSE #0 can have a ChargingStation MaxProfile, ChargingStation
          ExternalConstraints, LocalGeneration or a TxDefaultProfile. / Note, that a TxDefaultProfile is not
          applied to EVSE #0 but to all individual EVSEs (see K01.FR.14). |
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from smart_charging import (
    CHARGING_LIMIT_SOURCE,
    CHARGING_PROFILE_PURPOSE,
    reported_profile,
    request_charging_profiles_report,
    validate_get_charging_profiles,
)
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_29(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: EnergyTransferStarted
    await energy_transfer_started(cp)

    # 1. The CSMS sends a GetChargingProfilesRequest with
    #    - evseId 0
    # 2. The Test System responds with a GetChargingProfilesResponse with
    #    - status Accepted
    request = await request_charging_profiles_report(
        cp, evse_id=0, chargingProfilePurpose=CHARGING_PROFILE_PURPOSE)
    # evseId 0, chargingProfile.chargingProfilePurpose <Configured chargingProfilePurpose>;
    # stackLevel, chargingLimitSource and chargingProfileId must be omitted
    validate_get_charging_profiles(request, evse_id=0, purpose=CHARGING_PROFILE_PURPOSE)

    # 3. The Test System sends a ReportChargingProfilesRequest with
    #    - requestId <Received requestId>
    # 4. The CSMS responds with a ReportChargingProfilesResponse
    await cp.call(call.ReportChargingProfiles(
        request_id=request.request_id,
        charging_limit_source=CHARGING_LIMIT_SOURCE,
        evse_id=0,
        charging_profile=[reported_profile()],
    ))

    start_task.cancel()
