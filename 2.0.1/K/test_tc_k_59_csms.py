"""
TC_K_59 - Renegotiating a Charging Schedule - Initiated by CSMS - Send NotifyEVChargingNeeds
Use case: K16 | Requirements: K16.FR.12
K16.FR.12: AND Charging Station sends a NotifyEVChargingNeed sRequest The CSMS SHALL send a SetChargingProfileRequest. This situation is not desirable, because charging profile will likely be the same as in
    Precondition: K16.FR.09 AND Charging Station sends a NotifyEVChargingNeedsRequest
System under test: CSMS

Description:
    The CSMS sends a SetChargingProfileRequest to the Charging Station to influence the power or current
    drawn by the EV. The CSMS calculates a ChargingSchedule to stay within limits which MAY be imposed by
    an external system.

Purpose:
    To verify if the CSMS is able to handle a Charging Stations resending the charging needs of the EV.

Before:
    Reusable State(s): State is Authorized AND EVConnectedPreSession AND ISO15118SmartCharging

Main (8 steps):
    1. CSMS sends SetChargingProfileRequest
    2. CS responds with SetChargingProfileResponse (Accepted)
    3. CS sends NotifyEVChargingNeedsRequest
    4. CSMS responds with NotifyEVChargingNeedsResponse (Accepted or Processing)
    5. CSMS sends SetChargingProfileRequest
       Note: If NotifyEVChargingNeedsStatus was Processing, the OCTT will wait 60 seconds for the request
    6. CS responds with SetChargingProfileResponse (Accepted)
    7. CS sends NotifyEVChargingScheduleRequest (schedule from step 5)
    8. CSMS responds with NotifyEVChargingScheduleResponse (Accepted)

Tool validations:
    * Step 1: SetChargingProfileRequest evseId, purpose TxProfile, transactionId
    * Step 4: NotifyEVChargingNeedsResponse status Accepted or Processing
    * Step 5: SetChargingProfileRequest evseId, purpose TxProfile, transactionId
    * Step 8: NotifyEVChargingScheduleResponse status Accepted
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
    Action, RegistrationStatusEnumType, ConnectorStatusEnumType,
    ChargingProfileStatusEnumType, NotifyEVChargingNeedsStatusEnumType,
    GenericStatusEnumType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
    ChargingProfilePurposeEnumType, EnergyTransferModeEnumType,
)
from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context
from reusable_states.authorized import authorized
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from trigger import send_call
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)


def get_field(d, snake, camel):
    v = d.get(snake)
    return v if v is not None else d.get(camel)


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
            'evse_id': evse_id, 'charging_profile': charging_profile,
        })
        self._set_charging_profile_count += 1
        if self._set_charging_profile_count == 1:
            self._first_profile_received.set()
        elif self._set_charging_profile_count >= 2:
            self._second_profile_received.set()
        return call_result.SetChargingProfile(status=ChargingProfileStatusEnumType.accepted)


async def _execute_iso15118_smart_charging(cp, transaction_id):
    """Execute reusable state ISO15118SmartCharging."""
    needs_payload = call.NotifyEVChargingNeeds(
        charging_needs={'requested_energy_transfer': EnergyTransferModeEnumType.ac_three_phase},
        evse_id=EVSE_ID, max_schedule_tuples=10,
    )
    needs_response = await cp.call(needs_payload)
    assert needs_response.status in (
        NotifyEVChargingNeedsStatusEnumType.accepted, NotifyEVChargingNeedsStatusEnumType.processing,
    )

    await asyncio.wait_for(cp._first_profile_received.wait(), timeout=CSMS_ACTION_TIMEOUT)
    cp._first_profile_received.clear()

    profile = cp._set_charging_profile_requests[-1]['charging_profile']
    schedules = get_field(profile, 'charging_schedule', 'chargingSchedule')
    schedule = schedules[0] if isinstance(schedules, list) else schedules

    notify_sched = call.NotifyEVChargingSchedule(
        time_base=now_iso(), charging_schedule=schedule, evse_id=EVSE_ID,
    )
    await cp.call(notify_sched)

    event = TransactionEvent(
        event_type=TransactionEventType.updated, timestamp=now_iso(),
        trigger_reason=TriggerReasonType.charging_state_changed,
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': ChargingStateType.charging},
        evse={'id': EVSE_ID, 'connector_id': CONNECTOR_ID},
    )
    await cp.send_transaction_event_request(event)


@pytest.mark.asyncio
async def test_tc_k_59():
    """Renegotiating a Charging Schedule - Initiated by CSMS - Send NotifyEVChargingNeeds."""
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

    # Before: Authorized + EVConnectedPreSession + ISO15118SmartCharging
    await ev_connected_pre_session(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                     ev_connected_pre_session=True)
    await _execute_iso15118_smart_charging(cp, transaction_id)

    # Main scenario - CSMS-initiated renegotiation with NotifyEVChargingNeeds

    # Step 1-2: Wait for CSMS to send SetChargingProfileRequest
    # Reset counter for the main phase (iso15118 already used 1 profile)
    cp._second_profile_received.clear()
    now = datetime.now(timezone.utc)
    async def trigger_renegotiation():
        await asyncio.sleep(1)
        await send_call(cp_id, "SetChargingProfile", {
            "evseId": EVSE_ID,
            "chargingProfile": {
                "id": 2,
                "stackLevel": 0,
                "chargingProfilePurpose": "TxProfile",
                "chargingProfileKind": "Relative",
                "transactionId": transaction_id,
                "chargingSchedule": [{
                    "id": 1,
                    "chargingRateUnit": "A",
                    "chargingSchedulePeriod": [{
                        "startPeriod": 0,
                        "limit": 10.0,
                    }],
                }],
            },
        })
    trigger_task = asyncio.create_task(trigger_renegotiation())
    await asyncio.wait_for(cp._second_profile_received.wait(), timeout=CSMS_ACTION_TIMEOUT)
    trigger_task.cancel()
    profile1 = cp._set_charging_profile_requests[-1]
    p1 = profile1['charging_profile']
    purpose1 = get_field(p1, 'charging_profile_purpose', 'chargingProfilePurpose')
    assert purpose1 in ('TxProfile', ChargingProfilePurposeEnumType.tx_profile)
    assert profile1['evse_id'] == EVSE_ID
    tx_id1 = get_field(p1, 'transaction_id', 'transactionId')
    assert tx_id1 == transaction_id

    # Step 3: CS sends NotifyEVChargingNeedsRequest (new charging needs from EV)
    needs_payload = call.NotifyEVChargingNeeds(
        charging_needs={'requested_energy_transfer': EnergyTransferModeEnumType.ac_three_phase},
        evse_id=EVSE_ID, max_schedule_tuples=10,
    )
    # Step 4: CSMS responds with NotifyEVChargingNeedsResponse
    needs_response = await cp.call(needs_payload)
    assert needs_response.status in (
        NotifyEVChargingNeedsStatusEnumType.accepted, NotifyEVChargingNeedsStatusEnumType.processing,
        'Accepted', 'Processing',
    )

    # Step 5-6: Wait for CSMS to send another SetChargingProfileRequest
    # Note: If NotifyEVChargingNeedsStatus was Processing, OCTT waits up to 60 seconds
    third_profile = asyncio.Event()
    original_count = cp._set_charging_profile_count

    async def _wait_for_third():
        while cp._set_charging_profile_count <= original_count:
            await asyncio.sleep(0.1)
        third_profile.set()

    wait_task = asyncio.create_task(_wait_for_third())
    await asyncio.wait_for(third_profile.wait(), timeout=CSMS_ACTION_TIMEOUT)
    wait_task.cancel()

    profile2 = cp._set_charging_profile_requests[-1]
    p2 = profile2['charging_profile']
    purpose2 = get_field(p2, 'charging_profile_purpose', 'chargingProfilePurpose')
    assert purpose2 in ('TxProfile', ChargingProfilePurposeEnumType.tx_profile)
    assert profile2['evse_id'] == EVSE_ID
    tx_id2 = get_field(p2, 'transaction_id', 'transactionId')
    assert tx_id2 == transaction_id

    # Step 7: CS sends NotifyEVChargingScheduleRequest (schedule from step 5)
    schedules = get_field(p2, 'charging_schedule', 'chargingSchedule')
    schedule = schedules[0] if isinstance(schedules, list) else schedules
    notify_sched = call.NotifyEVChargingSchedule(
        time_base=now_iso(), charging_schedule=schedule, evse_id=EVSE_ID,
    )
    # Step 8: CSMS responds with NotifyEVChargingScheduleResponse (Accepted)
    sched_response = await cp.call(notify_sched)
    assert sched_response.status in (GenericStatusEnumType.accepted, 'Accepted')

    logging.info("TC_K_59 completed successfully")
    start_task.cancel()
    await ws.close()
