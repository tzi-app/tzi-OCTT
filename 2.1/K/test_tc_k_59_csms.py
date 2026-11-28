"""
Test case name      Renegotiating a Charging Schedule ISO 15118-2 - Initiated by CSMS - Send
                    NotifyEVChargingNeeds
Test case Id        TC_K_59_CSMS
Use case Id(s)      K16
Requirement(s)      K16.FR.12

Requirement Details:
    K16.FR.12: The CSMS SHALL send a SetChargingProfileRequest.
        Precondition: K16.FR.09 AND Charging Station sends a NotifyEVChargingNeedsRequest
        Note: This situation is not desirable, because charging profile will likely be the same as in
              K16.FR.01, but this is added for robustness when Charging Station is not adhering to K16.FR.09.
System under test   CSMS

Description         The CSMS sends a SetChargingProfileRequest to the Charging Station to influence the power
                    or current drawn by the EV. The CSMS calculates a ChargingSchedule to stay within limits
                    which MAY be imposed by an external system.

Purpose             To verify if the CSMS is able to handle a Charging Stations resending the charging needs
                    of the EV.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is
                    Authorized AND
                    EVConnectedPreSession AND
                    ISO15118SmartCharging

Test Scenario
Manual Action: Trigger SetChargingProfile
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse
    - With status Accepted
3. The Test System sends a NotifyEVChargingNeedsRequest.
    - With evseId <Configured evseId>
    - maxScheduleTuples & chargingNeeds <Configured values from mock EV>
4. The CSMS responds with a NotifyEVChargingNeedsResponse.
5. The CSMS sends a SetChargingProfileRequest
    Note(s):
    - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
      request
6. The Test System responds with a SetChargingProfileResponse
    - With status Accepted
7. The Test System sends a NotifyEVChargingScheduleRequest.
    - With evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 3>
8. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 1:
    (Message: SetChargingProfileRequest)
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 4:
    (Message: NotifyEVChargingNeedsResponse)
    - status Accepted or Processing
* Step 5:
    (Message: SetChargingProfileRequest)
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 8:
    (Message: NotifyEVChargingScheduleResponse)
    - status Accepted

Post scenario validations:
    N/a

Remarks
The section heading is printed as "TC_K_59_CSMS: Renegotiating a Charging Schedule ISO 15118-20 - Initiated by
CSMS - Send NotifyEVChargingNeeds" (ISO 15118-20), while the Test case name cell is printed with "ISO
15118-2".
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.authorized import authorized
from reusable_states.booted import booted
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from reusable_states.iso15118_smart_charging import (
    charging_needs,
    iso15118_smart_charging,
    negotiate_charging_schedule,
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
async def test_tc_k_59(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State(s): [not printed in the test case] A charging schedule is renegotiated, so
    # there is an authorized transaction of a connected EV that has a charging schedule: State is
    # Authorized, EVConnectedPreSession and ISO15118SmartCharging.
    transaction_id = await authorized(cp)
    await ev_connected_pre_session(cp)
    current = await iso15118_smart_charging(cp)

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

    # 3. The Test System sends a NotifyEVChargingNeedsRequest.
    #    - With evseId <Configured evseId>
    #    - maxScheduleTuples & chargingNeeds <Configured values from mock EV>
    # 4. The CSMS responds with a NotifyEVChargingNeedsResponse.
    #    - status Accepted or Processing
    # 5. The CSMS sends a SetChargingProfileRequest
    #    Note(s): If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will
    #    wait 60 seconds for the request
    #    - evseId <Configured evseId>, chargingProfilePurpose TxProfile, transactionId <Provided
    #      transactionId from before>
    # 6. The Test System responds with a SetChargingProfileResponse
    #    - With status Accepted
    request = await negotiate_charging_schedule(cp, charging_needs('iso15118-2'))

    # 7. The Test System sends a NotifyEVChargingScheduleRequest.
    #    - With evseId <Configured evseId>
    #    - chargingSchedule <the ChargingSchedule that the CSMS provided, at step 5>
    # 8. The CSMS responds with a NotifyEVChargingScheduleResponse.
    #    - status Accepted
    await notify_ev_charging_schedule(cp, request.charging_profile.charging_schedule[0])

    start_task.cancel()
