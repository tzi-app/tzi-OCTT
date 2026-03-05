"""
TC_K_57 - Renegotiating a Charging Schedule - Initiated by EV
Use case: K17 | Requirements: K17.FR.02,K17.FR.03,K17.FR.05,K17.FR.07,K17.FR.11
K17.FR.02: In response to a NotifyEVChargingNeedsRequest the CSMS SHALL send a NotifyEVChargingNeedsResponse.
    Precondition: K17.FR.01
K17.FR.03: K17.FR.02 AND If the CSMS is able to provide a charging schedule now CSMS SHALL indicate this by setting the status field in the NotifyEVChargingNeedsResponse to 'Accepted'.
    Precondition: K17.FR.02 AND If the CSMS is able to provide a charging schedule now
K17.FR.05: K17.FR.02 AND If the CSMS is able to provide a charging schedule, but needs processing time CSMS SHALL indicate this by setting the status field in the NotifyEVChargingNeedsResponse to 'Processing'.
    Precondition: K17.FR.02 AND If the CSMS is able to provide a charging schedule, but needs processing time
K17.FR.07: AND EV returns a charging profile Charging Station SHALL verify that provided charging profile is within boundaries of the ChargingSchedule from CSMS. In ISO 15118 EV can sent its charging profile as part of PowerDeliveryReq.
    Precondition: K17.FR.03 or K17.FR.05
K17.FR.11: AND EV charging profile is within limits of CSMS ChargingSchedule CSMS responds with NotifyEVChargingScheduleResponse with status Accepted to Charging Station. Note: Already checked by Charging Station, but CSMS does its own check.
    Precondition: K17.FR.10 AND EV charging profile is within limits of CSMS ChargingSchedule
System under test: CSMS

Description:
    The EV signals the Charging Station that it wants to renegotiate and it provides new charging needs,
    which the Charging Station sends to the CSMS. Based on this and other parameters, the CSMS calculates a
    new charging schedule and sends it via SetChargingProfileRequest to Charging Station.

Before:
    Reusable State(s): State is Authorized AND EVConnectedPreSession AND ISO15118SmartCharging

Main (6 steps):
    1. CS sends NotifyEVChargingNeedsRequest
    2. CSMS responds with NotifyEVChargingNeedsResponse (Accepted or Processing)
    3. CSMS sends SetChargingProfileRequest (TxProfile)
       Note: If NotifyEVChargingNeedsResponseStatus was Processing, OCTT waits up to 60 seconds
    4. CS responds with SetChargingProfileResponse (Accepted)
    5. CS sends NotifyEVChargingScheduleRequest (schedule from step 3)
    6. CSMS responds with NotifyEVChargingScheduleResponse (Accepted)

Tool validations:
    * Step 2: NotifyEVChargingNeedsResponse status Accepted or Processing
    * Step 3: SetChargingProfileRequest evseId, purpose TxProfile, transactionId
    * Step 6: NotifyEVChargingScheduleResponse status Accepted
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
        self._profile_received = asyncio.Event()

    @on(Action.set_charging_profile)
    async def on_set_charging_profile(self, evse_id, charging_profile, **kwargs):
        logging.info(f"Received SetChargingProfileRequest #{self._set_charging_profile_count + 1}")
        self._set_charging_profile_requests.append({
            'evse_id': evse_id, 'charging_profile': charging_profile,
        })
        self._set_charging_profile_count += 1
        self._profile_received.set()
        return call_result.SetChargingProfile(status=ChargingProfileStatusEnumType.accepted)


async def _execute_iso15118_smart_charging(cp, transaction_id):
    """Execute reusable state ISO15118SmartCharging."""
    # Step 1: NotifyEVChargingNeedsRequest
    needs_payload = call.NotifyEVChargingNeeds(
        charging_needs={'requested_energy_transfer': EnergyTransferModeEnumType.ac_three_phase},
        evse_id=EVSE_ID, max_schedule_tuples=10,
    )
    needs_response = await cp.call(needs_payload)
    assert needs_response.status in (
        NotifyEVChargingNeedsStatusEnumType.accepted, NotifyEVChargingNeedsStatusEnumType.processing,
    )

    # Wait for SetChargingProfileRequest
    await asyncio.wait_for(cp._profile_received.wait(), timeout=CSMS_ACTION_TIMEOUT)
    cp._profile_received.clear()

    profile = cp._set_charging_profile_requests[-1]['charging_profile']
    schedules = get_field(profile, 'charging_schedule', 'chargingSchedule')
    schedule = schedules[0] if isinstance(schedules, list) else schedules

    # NotifyEVChargingScheduleRequest
    notify_sched = call.NotifyEVChargingSchedule(
        time_base=now_iso(), charging_schedule=schedule, evse_id=EVSE_ID,
    )
    await cp.call(notify_sched)

    # TransactionEvent (Charging)
    event = TransactionEvent(
        event_type=TransactionEventType.updated, timestamp=now_iso(),
        trigger_reason=TriggerReasonType.charging_state_changed,
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': ChargingStateType.charging},
        evse={'id': EVSE_ID, 'connector_id': CONNECTOR_ID},
    )
    await cp.send_transaction_event_request(event)


@pytest.mark.asyncio
async def test_tc_k_57():
    """Renegotiating a Charging Schedule - Initiated by EV."""
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

    # Main scenario - EV-initiated renegotiation

    # Step 1: CS sends NotifyEVChargingNeedsRequest (new needs)
    needs_payload = call.NotifyEVChargingNeeds(
        charging_needs={'requested_energy_transfer': EnergyTransferModeEnumType.ac_three_phase},
        evse_id=EVSE_ID, max_schedule_tuples=10,
    )
    # Step 2: CSMS responds with NotifyEVChargingNeedsResponse
    needs_response = await cp.call(needs_payload)
    assert needs_response.status in (
        NotifyEVChargingNeedsStatusEnumType.accepted, NotifyEVChargingNeedsStatusEnumType.processing,
    )

    # Step 3-4: Wait for CSMS SetChargingProfileRequest
    # Note: If NotifyEVChargingNeedsResponseStatus was Processing, OCTT waits up to 60 seconds
    cp._profile_received.clear()
    await asyncio.wait_for(cp._profile_received.wait(), timeout=CSMS_ACTION_TIMEOUT)
    profile = cp._set_charging_profile_requests[-1]
    p = profile['charging_profile']
    purpose = get_field(p, 'charging_profile_purpose', 'chargingProfilePurpose')
    assert purpose in ('TxProfile', ChargingProfilePurposeEnumType.tx_profile)
    assert profile['evse_id'] == EVSE_ID
    tx_id = get_field(p, 'transaction_id', 'transactionId')
    assert tx_id == transaction_id, \
        f"Expected transactionId={transaction_id}, got {tx_id}"

    # Step 5: CS sends NotifyEVChargingScheduleRequest (schedule from step 3)
    schedules = get_field(p, 'charging_schedule', 'chargingSchedule')
    schedule = schedules[0] if isinstance(schedules, list) else schedules
    notify_sched = call.NotifyEVChargingSchedule(
        time_base=now_iso(), charging_schedule=schedule, evse_id=EVSE_ID,
    )
    # Step 6: CSMS responds with NotifyEVChargingScheduleResponse (Accepted)
    sched_response = await cp.call(notify_sched)
    assert sched_response.status in (GenericStatusEnumType.accepted, 'Accepted')

    logging.info("TC_K_57 completed successfully")
    start_task.cancel()
    await ws.close()
