"""
TC_K_58 - Renegotiating a Charging Schedule - Initiated by CSMS
Use case: K16 | Requirements: K16.FR.06
K16.FR.06: AND EV charging profile is within limits of CSMS ChargingSchedule CSMS responds with NotifyEVChargingScheduleResponse with status Accepted to Charging Station. Note: Already checked by Charging Station, but CSMS does its own check.
    Precondition: K16.FR.05 AND EV charging profile is within limits of CSMS ChargingSchedule
System under test: CSMS

Description:
    The CSMS sends a SetChargingProfileRequest to the Charging Station to influence the power or current
    drawn by the EV. The CSMS calculates a ChargingSchedule to stay within limits which MAY be imposed by
    an external system.

Purpose:
    To verify if the CSMS is able to renegotiate power/current drawn by the EV.

Before:
    Reusable State(s): State is Authorized AND EVConnectedPreSession AND ISO15118SmartCharging

Main (4 steps):
    1. CSMS sends SetChargingProfileRequest
    2. CS responds with SetChargingProfileResponse (Accepted)
    3. CS sends NotifyEVChargingScheduleRequest (schedule from step 1)
    4. CSMS responds with NotifyEVChargingScheduleResponse (Accepted)

Tool validations:
    * Step 1: SetChargingProfileRequest evseId, purpose TxProfile, transactionId
    * Step 4: NotifyEVChargingScheduleResponse status Accepted
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
    ChargingProfileStatusEnumType, GenericStatusEnumType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
    ChargingProfilePurposeEnumType, EnergyTransferModeEnumType,
)
from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso
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
    needs_payload = call.NotifyEVChargingNeeds(
        charging_needs={'requested_energy_transfer': EnergyTransferModeEnumType.ac_three_phase},
        evse_id=EVSE_ID, max_schedule_tuples=10,
    )
    needs_response = await cp.call(needs_payload)

    await asyncio.wait_for(cp._profile_received.wait(), timeout=CSMS_ACTION_TIMEOUT)
    cp._profile_received.clear()

    profile = cp._set_charging_profile_requests[-1]['charging_profile']
    schedules = profile.get('charging_schedule') or profile.get('chargingSchedule')
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
async def test_tc_k_58():
    """Renegotiating a Charging Schedule - Initiated by CSMS."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ws = await websockets.connect(uri=uri, subprotocols=['ocpp2.0.1'], extra_headers=headers)
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

    # Main: CSMS-initiated renegotiation

    # Step 1-2: Wait for CSMS to send SetChargingProfileRequest
    cp._profile_received.clear()
    await asyncio.wait_for(cp._profile_received.wait(), timeout=CSMS_ACTION_TIMEOUT)
    profile = cp._set_charging_profile_requests[-1]
    p = profile['charging_profile']
    purpose = p.get('charging_profile_purpose') or p.get('chargingProfilePurpose')
    assert purpose in ('TxProfile', ChargingProfilePurposeEnumType.tx_profile)
    assert profile['evse_id'] == EVSE_ID
    tx_id = p.get('transaction_id') or p.get('transactionId')
    assert tx_id == transaction_id, \
        f"Expected transactionId={transaction_id}, got {tx_id}"

    # Step 3: CS sends NotifyEVChargingScheduleRequest (schedule from step 1)
    schedules = p.get('charging_schedule') or p.get('chargingSchedule')
    schedule = schedules[0] if isinstance(schedules, list) else schedules
    notify_sched = call.NotifyEVChargingSchedule(
        time_base=now_iso(), charging_schedule=schedule, evse_id=EVSE_ID,
    )
    # Step 4: CSMS responds with NotifyEVChargingScheduleResponse (Accepted)
    sched_response = await cp.call(notify_sched)
    assert sched_response.status in (GenericStatusEnumType.accepted, 'Accepted')

    logging.info("TC_K_58 completed successfully")
    start_task.cancel()
    await ws.close()
