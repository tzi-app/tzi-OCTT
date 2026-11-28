"""
Test case name      Renegotiating a Charging Schedule ISO 15118-20 - Initiated by CSMS
Test case Id        TC_K_113_CSMS
Use case Id(s)      K16
Requirement(s)      K16.FR.06

Requirement Details:
    K16.FR.06: CSMS responds with NotifyEVChargingScheduleResponse with status Accepted to Charging Station.
        Precondition: K16.FR.05 AND EV charging profile is within limits of CSMS ChargingSchedule
        Note: Note: Already checked by Charging Station, but CSMS does its own check.
System under test   CSMS

Description         The CSMS sends a SetChargingProfileRequest to the Charging Station to influence the power
                    or current drawn by the EV. The CSMS calculates a ChargingSchedule to stay within limits
                    which MAY be imposed by an external system.

Purpose             To verify if the CSMS is able to renegotiate power/current drawn by the EV.

Prerequisite(s)     CSMS supports ISO 15118-20

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized
                    State is EVConnectedPreSession
                    State is ISO15118SmartCharging (iso15118-20)

Test Scenario
Manual Action: Trigger SetChargingProfile
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse
    - With status Accepted
3. The Test System sends a NotifyEVChargingScheduleRequest.
    - With evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 1>
4. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 1:
    (Message: SetChargingProfileRequest)
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 4:
    (Message: NotifyEVChargingScheduleResponse)
    - status Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.authorized import authorized
from reusable_states.booted import booted
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from reusable_states.iso15118_20_transaction_just_started import V2X_VARIABLES
from reusable_states.iso15118_smart_charging import (
    iso15118_smart_charging,
    notify_ev_charging_schedule,
    validate_tx_profile,
)
from smart_charging import charging_profile, request_charging_profile
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_113(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # The Test System supports ISO 15118-20.
    cp.variables = dict(V2X_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State(s): State is Authorized, State is EVConnectedPreSession, State is
    #                    ISO15118SmartCharging (iso15118-20)
    transaction_id = await authorized(cp)
    await ev_connected_pre_session(cp)
    current = await iso15118_smart_charging(cp, 'iso15118-20')

    # Manual Action: Trigger SetChargingProfile
    #     - evseId <Configured evseId>
    #     - chargingProfilePurpose TxProfile
    #     - transactionId <Provided transactionId from before>
    # 1. The CSMS sends a SetChargingProfileRequest
    # 2. The Test System responds with a SetChargingProfileResponse
    #    - With status Accepted
    # The new TxProfile replaces the one of the transaction: it has its id (K01.FR.05, K01.FR.39).
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, charging_profile(
        'TxProfile', 'Absolute', 6, profile_id=current.charging_profile.id,
        transactionId=transaction_id))
    validate_tx_profile(request, transaction_id)

    # 3. The Test System sends a NotifyEVChargingScheduleRequest.
    #    - With evseId <Configured evseId>
    #    - chargingSchedule <ChargingSchedule provided at step 1>
    # 4. The CSMS responds with a NotifyEVChargingScheduleResponse.
    #    - status Accepted
    await notify_ev_charging_schedule(
        cp, request.charging_profile.charging_schedule[0], selected=True)

    start_task.cancel()
