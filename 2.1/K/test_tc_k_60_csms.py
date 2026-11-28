"""
Test case name      Set Charging Profile - TxProfile with ongoing transaction on the specified EVSE
Test case Id        TC_K_60_CSMS
Use case Id(s)      K01
Requirement(s)      K01.FR.03, K01.FR.31

Requirement Details:
    K01.FR.03: The CSMS SHALL include the transactionId in the SetChargingProfileRequest when setting a
               TxProfile.
        Note: The transactionId is used to match the profile to a specific transaction.
    K01.FR.31: The startPeriod of the first chargingSchedulePeriod in a chargingSchedule SHALL always be 0.
System under test   CSMS

Description         The CSMS sets a TxProfile on a specific EVSE for a currently ongoing transaction.

Purpose             To verify if the CSMS is able to exchange messages to set a TxProfile on a specific EVSE
                    for a currently ongoing transaction.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse
    With status is Accepted

Tool validations
* Step 1:
    (Message: SetChargingProfileRequest)
    chargingProfile.chargingProfilePurpose is TxProfile AND
    chargingProfile.evseId is <Configured evseId> AND
    chargingProfile.transactionId <Generated transactionId> AND
    chargingProfile.chargingProfileKind is Relative OR Absolute
    If chargingProfileKind is Relative then chargingSchedule.startSchedule must be omitted.
    If chargingProfileKind is Absolute then chargingSchedule.startSchedule must NOT be omitted.

    The received Charging Profile must comply with the requirements defined at part 2 specification.

Post scenario validations:
    N/a

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
from reusable_states.energy_transfer_started import energy_transfer_started
from smart_charging import (
    charging_profile,
    request_charging_profile,
    validate_part_2_requirements,
    validate_profile,
    validate_start_schedule_for_kind,
)
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_60(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # 1. The CSMS sends a SetChargingProfileRequest
    # 2. The Test System responds with a SetChargingProfileResponse With status is Accepted
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, charging_profile(
        'TxProfile', 'Relative', 6, duration=False, transactionId=transaction_id))

    # chargingProfilePurpose is TxProfile, evseId is <Configured evseId>, transactionId
    # <Generated transactionId>, chargingProfileKind is Relative OR Absolute
    validate_profile(request, evse_id=CONFIGURED_EVSE_ID, purpose='TxProfile',
                     kind=('Relative', 'Absolute'), stack_level=None, transaction_id=transaction_id)
    # If chargingProfileKind is Relative then chargingSchedule.startSchedule must be omitted. If
    # it is Absolute then it must NOT be omitted.
    validate_start_schedule_for_kind(request.charging_profile)
    # The received Charging Profile must comply with the requirements defined at part 2
    # specification.
    validate_part_2_requirements(request.charging_profile, evse_id=request.evse_id)

    start_task.cancel()
