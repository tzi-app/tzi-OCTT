"""
Test case name      Charging with load leveling based on High Level Communication - EV charging profile
                    exceeds limits
Test case Id        TC_K_55_CSMS
Use case Id(s)      K15,K16,K17
Requirement(s)      K15.FR.12, K15.FR.13, K16.FR.07, K16.FR.08, K17.FR.12, K17.FR.13

Requirement Details:
    K15.FR.12: CSMS responds with NotifyEVChargingScheduleResponse with status Rejected to Charging Station.
        Precondition: K15.FR.10 AND EV charging profile is NOT within limits of CSMS ChargingSchedule
    K15.FR.13: CSMS starts new renegotiation as per use case K16.
        Precondition: K15.FR.12
    K16.FR.07: CSMS responds with NotifyEVChargingScheduleResponse with status Rejected to Charging Station.
        Precondition: K16.FR.05 AND EV charging profile is NOT within limits of CSMS ChargingSchedule
    K16.FR.08: CSMS starts new renegotiation as per use case K16.
        Precondition: K16.FR.07
    K17.FR.12 (2.1): CSMS responds with NotifyEVChargingScheduleResponse with status Rejected to Charging
                     Station.
        Precondition: K17.FR.10 AND EV charging profile is NOT within limits of CSMS ChargingSchedule
        Note: Not applicable in dynamic control mode.
    K17.FR.13: CSMS starts new renegotiation as per use case K16.
        Precondition: K17.FR.12
System under test   CSMS

Description         ISO15118-1 E1 AC Charging with load leveling based on High Level Communication, and E4 DC
                    charging with load leveling based on High Level Communication.

Purpose             To verify if the CSMS is able to renegotiate when it receives the EV charging schedule
                    which exceeds the profile limits.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized
                    State is EVConnectedPreSession

Test Scenario
1. The Test System sends a NotifyEVChargingNeedsRequest.
    - evseId <Configured evseId>
    - maxScheduleTuples & chargingNeeds <Configured values from mock EV>
2. The CSMS responds with a NotifyEVChargingNeedsResponse.
3. The CSMS sends a SetChargingProfileRequest
4. The Test System responds with a SetChargingProfileResponse
    - status Accepted
5. The Test System sends a NotifyEVChargingScheduleRequest.
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule that exceeds the limits of the chargingSchedule provided at step 3.>
6. The CSMS responds with a NotifyEVChargingScheduleResponse.
7. The Test System sends a TransactionEventRequest.
    - triggerReason ChargingStateChanged
    - transactionInfo.chargingState Charging
8. The CSMS responds with a TransactionEventResponse.
9. The CSMS sends a SetChargingProfileRequest
10. The Test System responds with a SetChargingProfileResponse
    - status Accepted
11. The Test System sends a NotifyEVChargingScheduleRequest.
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 9>
12. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 2:
    Message NotifyEVChargingNeedsResponse
    - status Accepted
* Step 3:
    Message SetChargingProfileRequest
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 6:
    Message NotifyEVChargingScheduleResponse
    - status Rejected
* Step 9:
    Message SetChargingProfileRequest
    - evseId <Configured evseId>
    - chargingProfilePurpose TxProfile
    - transactionId <Provided transactionId from before>
* Step 12:
    Message NotifyEVChargingScheduleResponse
    - status Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.authorized import authorized
from reusable_states.booted import booted
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from reusable_states.iso15118_smart_charging import (
    charging_needs,
    negotiate_charging_schedule,
    notify_ev_charging_schedule,
    validate_tx_profile,
)
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


def exceeding(schedule):
    """The charging schedule of an EV that takes more than the charging schedule of the CSMS
    allows: every period has twice its limit, and more."""
    periods = [dict(period, limit=(period.limit or period.setpoint or 0) * 2 + 1000)
               for period in schedule.charging_schedule_period]
    return dict(schedule, charging_schedule_period=periods)


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_55(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is Authorized
    transaction_id = await authorized(cp)
    # The charging needs come from an EV over ISO 15118: the EV is connected to the EVSE.
    await ev_connected_pre_session(cp)

    # 1. The Test System sends a NotifyEVChargingNeedsRequest.
    #    - evseId <Configured evseId>
    #    - maxScheduleTuples & chargingNeeds <Configured values from mock EV>
    # 2. The CSMS responds with a NotifyEVChargingNeedsResponse.
    #    - status Accepted
    # 3. The CSMS sends a SetChargingProfileRequest
    #    - evseId <Configured evseId>, chargingProfilePurpose TxProfile, transactionId <Provided
    #      transactionId from before>
    # 4. The Test System responds with a SetChargingProfileResponse
    #    - status Accepted
    first = await negotiate_charging_schedule(cp, charging_needs('iso15118-2'), statuses=('Accepted',))

    # 5. The Test System sends a NotifyEVChargingScheduleRequest.
    #    - evseId <Configured evseId>
    #    - chargingSchedule <ChargingSchedule that exceeds the limits of the chargingSchedule
    #      provided at step 3.>
    # 6. The CSMS responds with a NotifyEVChargingScheduleResponse.
    #    - status Rejected
    # Only a SetChargingProfileRequest that follows the rejection is the one of step 9.
    cp.forget_requests('SetChargingProfile')
    await notify_ev_charging_schedule(
        cp, exceeding(first.charging_profile.charging_schedule[0]), status='Rejected')

    # 7. The Test System sends a TransactionEventRequest.
    #    - triggerReason ChargingStateChanged
    #    - transactionInfo.chargingState Charging
    # 8. The CSMS responds with a TransactionEventResponse.
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='ChargingStateChanged',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'Charging'},
    ))

    # 9. The CSMS sends a SetChargingProfileRequest
    #    - evseId <Configured evseId>, chargingProfilePurpose TxProfile, transactionId <Provided
    #      transactionId from before>
    # 10. The Test System responds with a SetChargingProfileResponse
    #     - status Accepted
    second = await cp.wait_for_request('SetChargingProfile')
    validate_tx_profile(second, transaction_id)

    # 11. The Test System sends a NotifyEVChargingScheduleRequest.
    #     - evseId <Configured evseId>
    #     - chargingSchedule <ChargingSchedule provided at step 9>
    # 12. The CSMS responds with a NotifyEVChargingScheduleResponse.
    #     - status Accepted
    await notify_ev_charging_schedule(cp, second.charging_profile.charging_schedule[0])

    start_task.cancel()
