"""
Test case name      Set Charging Profile - ChargingStationMaxProfile
Test case Id        TC_K_03_CSMS
Use case Id(s)      K01
Requirement(s)      K01.FR.31, K01.FR.38

Requirement Details:
    K01.FR.31: The startPeriod of the first chargingSchedulePeriod in a chargingSchedule SHALL always be 0.
    K01.FR.38: chargingProfileKind SHALL NOT be Relative
        Precondition: When chargingProfilePurpose = ChargingStationMaxProfile
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to send a ChargingStationMaxProfile charging profile as
                    described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a SetChargingProfileRequest
    - chargingProfile.id <Configured chargingProfileId>
2. The Test System responds with a SetChargingProfileResponse with status Accepted

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - evseId 0 AND
    - chargingProfile.stackLevel <Configured stackLevel> AND
    - chargingProfile.chargingProfilePurpose ChargingStationMaxProfile AND
    - chargingProfile.chargingProfileKind Absolute
    - chargingProfile.chargingSchedule.chargingRateUnit <Configured ChargingRateUnit>
    - chargingProfile.chargingSchedule.duration <Configured duration>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 8.0 or 8000.0
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.numberPhases <Configured numberPhases> where
      <Configured numberPhases> not 3 OR
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.numberPhases <Configured numberPhases> or <omit>
      where <Configured numberPhases> 3
    - chargingProfile.chargingSchedule.startSchedule <Not omitted>

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.14. Page 334 - (2026-09) - K01 - added missing requirement to reject ExternalConstraints from CSMS
        [1327]
        (Part 2 errata - applies to this test via use case K01)
        A CSMS is forbidden to send a ChargingStationExternalConstraints profile to a charging station, but a
        matching requirement that Charging Station must reject it if it receives such a charging profile was
        missing.

        New requirement

        | ID | Precondition | Requirement definition | Note |
        | K01.FR.62 | When a Charging Station receives a SetChargingProfileRequest from CSMS with
          chargingProfilePurpose set to ChargingStationExternalConstraints | Charging Station SHALL respond
          with a status = Rejected and optionally a statusInfo.reasonCode = UnsupportedPurpose | Purpose not
          allowed from CSMS. |

    2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] -
        2.16.2. Page 334 - Set Charging Profile
        (Part 2 errata - applies to this test via use case K01)
        Added a requirement that CSMS shall not send a LocalGeneration profile and a requirement that a
        Charging Station shall reject it.

        New requirements

        | ID | Precondition | Requirement definition | Note |
        | K01.FR.63 / (2.1) | | The CSMS SHALL NOT set chargingProfilePurpose to LocalGeneration in a
          SetChargingProfileRequest. | This purpose is only received from an external system. |
        | K01.FR.64 / (2.1) | When a Charging Station receives a SetChargingProfileRequest from CSMS with
          chargingProfilePurpose set to LocalGeneration | Charging Station SHALL respond with a status =
          Rejected and optionally a statusInfo.reasonCode = UnsupportedPurpose | Purpose not allowed from
          CSMS. |
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from smart_charging import (
    charging_profile,
    CHARGING_PROFILE_ID,
    only_schedule,
    request_charging_profile,
    validate_profile,
    validate_schedule,
)
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_03(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a SetChargingProfileRequest
    #    - chargingProfile.id <Configured chargingProfileId>
    # 2. The Test System responds with a SetChargingProfileResponse with status Accepted
    request = await request_charging_profile(
        cp, 0, charging_profile('ChargingStationMaxProfile', 'Absolute', 8))

    # evseId 0, stackLevel <Configured stackLevel>, chargingProfilePurpose
    # ChargingStationMaxProfile, chargingProfileKind Absolute
    validate_profile(request, evse_id=0, purpose='ChargingStationMaxProfile', kind='Absolute',
                     profile_id=CHARGING_PROFILE_ID)
    # chargingRateUnit <Configured ChargingRateUnit>, duration <Configured duration>,
    # chargingSchedulePeriod.startPeriod 0, .limit 8.0 or 8000.0, .numberPhases <Configured
    # numberPhases> (or omitted when that is 3), startSchedule <Not omitted>
    validate_schedule(only_schedule(request), amperes=8, start_schedule=True, duration=True)

    start_task.cancel()
