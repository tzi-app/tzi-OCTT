"""
TC_K_55 - Charging with load leveling - EV charging profile exceeds limits
Use case: K15,K16,K17 | Requirements: K15.FR.12,K15.FR.13,K16.FR.07,K16.FR.08,K17.FR.12,K17.FR.13
K15.FR.12: AND EV charging profile is NOT within limits of CSMS ChargingSchedule CSMS responds with NotifyEVChargingScheduleResponse with status Rejected to Charging Station.
    Precondition: K15.FR.10 AND EV charging profile is NOT within limits of CSMS ChargingSchedule
K15.FR.13: CSMS starts new renegotiation as per use case K16.
    Precondition: K15.FR.12
K16.FR.07: AND EV charging profile is NOT within limits of CSMS ChargingSchedule CSMS responds with NotifyEVChargingScheduleResponse with status Rejected to Charging Station.
    Precondition: K16.FR.05 AND EV charging profile is NOT within limits of CSMS ChargingSchedule
K16.FR.08: CSMS starts new renegotiation as per use case K16.
    Precondition: K16.FR.07
K17.FR.12: AND EV charging profile is NOT within limits of CSMS ChargingSchedule CSMS responds with NotifyEVChargingScheduleResponse with status Rejected to Charging Station.
    Precondition: K17.FR.10 AND EV charging profile is NOT within limits of CSMS ChargingSchedule
K17.FR.13: CSMS starts new renegotiation as per use case K16.
    Precondition: K17.FR.12
System under test: CSMS

Description:
    ISO15118-1 E1 AC Charging with load leveling based on High Level Communication, and E4 DC charging
    with load leveling based on High Level Communication.

Purpose:
    To verify if the CSMS is able to renegotiate when it receives the EV charging schedule which exceeds the
    profile limits.

Before:
    Reusable State(s): State is Authorized AND EVConnectedPreSession

Main (14 steps):
    1. CS sends NotifyEVChargingNeedsRequest
    2. CSMS responds with NotifyEVChargingNeedsResponse (status Accepted)
    3. CSMS sends SetChargingProfileRequest (TxProfile, transactionId)
    4. CS responds with SetChargingProfileResponse (Accepted)
    5. CS sends NotifyEVChargingScheduleRequest (exceeding limits of step 3)
    6. CSMS responds with NotifyEVChargingScheduleResponse (status Rejected)
    7. CS sends TransactionEventRequest (ChargingStateChanged, Charging)
    8. CSMS responds with TransactionEventResponse
    9. CSMS sends SetChargingProfileRequest (TxProfile, transactionId)
    10. CS responds with SetChargingProfileResponse (Accepted)
    11. CS sends NotifyEVChargingScheduleRequest (schedule from step 9)
    12. CSMS responds with NotifyEVChargingScheduleResponse (Accepted)
    13. CS sends TransactionEventRequest (ChargingRateChanged)
    14. CSMS responds with TransactionEventResponse

Tool validations:
    * Step 2: NotifyEVChargingNeedsResponse status Accepted
    * Step 3: SetChargingProfileRequest evseId, purpose TxProfile, transactionId
    * Step 6: NotifyEVChargingScheduleResponse status Rejected
    * Step 9: SetChargingProfileRequest evseId, purpose TxProfile, transactionId
    * Step 12: NotifyEVChargingScheduleResponse status Accepted
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.routing import on
from ocpp.v201 import call, call_result
from ocpp.v201.call import TransactionEvent
from ocpp.v201.enums import (
    Action,
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    ChargingProfileStatusEnumType,
    NotifyEVChargingNeedsStatusEnumType,
    GenericStatusEnumType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
    ChargingProfilePurposeEnumType,
    EnergyTransferModeEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context
from reusable_states.authorized import authorized
from reusable_states.ev_connected_pre_session import ev_connected_pre_session

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


class SmartChargingMockCP(TziChargePoint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_charging_profile_count = 0
        self._set_charging_profile_requests = []
        self._first_profile_received = asyncio.Event()
        self._second_profile_received = asyncio.Event()

    @on(Action.set_charging_profile)
    async def on_set_charging_profile(self, evse_id, charging_profile, **kwargs):
        logging.info(f"Received SetChargingProfileRequest #{self._set_charging_profile_count + 1}")
        self._set_charging_profile_requests.append({
            'evse_id': evse_id,
            'charging_profile': charging_profile,
        })
        self._set_charging_profile_count += 1
        if self._set_charging_profile_count == 1:
            self._first_profile_received.set()
        elif self._set_charging_profile_count >= 2:
            self._second_profile_received.set()
        return call_result.SetChargingProfile(
            status=ChargingProfileStatusEnumType.accepted
        )


@pytest.mark.asyncio
async def test_tc_k_55():
    """Charging with load leveling - EV charging profile exceeds limits."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
    ws = await websockets.connect(uri=uri, subprotocols=['ocpp2.0.1'], extra_headers=headers, ssl=ssl_ctx)
    time.sleep(0.5)

    cp = SmartChargingMockCP(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted
    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Before: Authorized + EVConnectedPreSession
    await ev_connected_pre_session(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                     ev_connected_pre_session=True)

    # Step 1: Send NotifyEVChargingNeedsRequest
    notify_needs_payload = call.NotifyEVChargingNeeds(
        charging_needs={
            'requested_energy_transfer': EnergyTransferModeEnumType.ac_three_phase,
        },
        evse_id=EVSE_ID,
        max_schedule_tuples=10,
    )
    # Step 2: CSMS responds (Accepted)
    needs_response = await cp.call(notify_needs_payload)
    assert needs_response.status in (NotifyEVChargingNeedsStatusEnumType.accepted, 'Accepted')

    # Step 3-4: Wait for first SetChargingProfileRequest from CSMS
    await asyncio.wait_for(cp._first_profile_received.wait(), timeout=CSMS_ACTION_TIMEOUT)
    profile1 = cp._set_charging_profile_requests[0]

    def get_field(d, snake, camel):
        v = d.get(snake)
        return v if v is not None else d.get(camel)

    # Validate step 3
    assert profile1['evse_id'] == EVSE_ID
    p1 = profile1['charging_profile']
    purpose1 = get_field(p1, 'charging_profile_purpose', 'chargingProfilePurpose')
    assert purpose1 in ('TxProfile', ChargingProfilePurposeEnumType.tx_profile)
    tx_id1 = get_field(p1, 'transaction_id', 'transactionId')
    assert tx_id1 == transaction_id

    # Step 5: Send NotifyEVChargingScheduleRequest that EXCEEDS limits of step 3
    schedules1 = get_field(p1, 'charging_schedule', 'chargingSchedule')
    schedule1 = schedules1[0] if isinstance(schedules1, list) else schedules1
    # Create an exceeding schedule by increasing the limit
    exceeding_schedule = dict(schedule1)
    periods = get_field(exceeding_schedule, 'charging_schedule_period', 'chargingSchedulePeriod')
    if periods:
        exceeding_periods = []
        for p in periods:
            ep = dict(p)
            ep['limit'] = ep.get('limit', 10.0) * 2  # Double the limit to exceed
            exceeding_periods.append(ep)
        if 'charging_schedule_period' in exceeding_schedule:
            exceeding_schedule['charging_schedule_period'] = exceeding_periods
        else:
            exceeding_schedule['chargingSchedulePeriod'] = exceeding_periods

    notify_schedule_payload = call.NotifyEVChargingSchedule(
        time_base=now_iso(),
        charging_schedule=exceeding_schedule,
        evse_id=EVSE_ID,
    )
    # Step 6: CSMS responds with Rejected
    schedule_response = await cp.call(notify_schedule_payload)
    assert schedule_response is not None
    assert schedule_response.status in (GenericStatusEnumType.rejected, 'Rejected')

    # Step 7-8: Send TransactionEventRequest (ChargingStateChanged, Charging)
    event1 = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.charging_state_changed,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.charging,
        },
        evse={'id': EVSE_ID, 'connector_id': CONNECTOR_ID},
    )
    event1_response = await cp.send_transaction_event_request(event1)
    assert event1_response is not None

    # Step 9-10: Wait for second SetChargingProfileRequest from CSMS
    await asyncio.wait_for(cp._second_profile_received.wait(), timeout=CSMS_ACTION_TIMEOUT)
    profile2 = cp._set_charging_profile_requests[1]

    # Validate step 9
    assert profile2['evse_id'] == EVSE_ID
    p2 = profile2['charging_profile']
    purpose2 = get_field(p2, 'charging_profile_purpose', 'chargingProfilePurpose')
    assert purpose2 in ('TxProfile', ChargingProfilePurposeEnumType.tx_profile)
    tx_id2 = get_field(p2, 'transaction_id', 'transactionId')
    assert tx_id2 == transaction_id

    # Step 11: Send NotifyEVChargingScheduleRequest with schedule from step 9
    schedules2 = get_field(p2, 'charging_schedule', 'chargingSchedule')
    schedule2 = schedules2[0] if isinstance(schedules2, list) else schedules2

    notify_schedule2_payload = call.NotifyEVChargingSchedule(
        time_base=now_iso(),
        charging_schedule=schedule2,
        evse_id=EVSE_ID,
    )
    # Step 12: CSMS responds with Accepted
    schedule2_response = await cp.call(notify_schedule2_payload)
    assert schedule2_response is not None
    assert schedule2_response.status in (GenericStatusEnumType.accepted, 'Accepted')

    logging.info("TC_K_55 completed successfully")
    start_task.cancel()
    await ws.close()
