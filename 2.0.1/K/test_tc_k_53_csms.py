"""
TC_K_53 - Charging with load leveling based on High Level Communication - Success
Use case: K15 | Requirements: K15.FR.02,K15.FR.03,K15.FR.05,K15.FR.07,K15.FR.11
K15.FR.02: In response to a NotifyEVChargingNeedsRequest the CSMS SHALL send a NotifyEVChargingNeedsResponse.
    Precondition: K15.FR.01
K15.FR.03: If the CSMS is able to provide a charging schedule, it SHALL indicate this by setting the status field in the NotifyEVChargingNeedsResponse to Accepted.
    Precondition: K15.FR.02
K15.FR.05: If the CSMS is able to provide a charging schedule; but needs processing time, it SHALL indicate this by setting the status field in the NotifyEVChargingNeedsResponse to Processing. The Charging Station does not have to wait for the SetChargingProfileRequest. CSMS will send it later and trigger a renegotiation as per use case K16.
    Precondition: K15.FR.02
K15.FR.07: AND EV returns a charging profile Charging Station SHALL verify that provided charging profile is within boundaries of the ChargingSchedule from CSMS. In ISO 15118 EV can sent its charging profile as part of PowerDeliveryReq.
    Precondition: K15.FR.03 or K15.FR.05
K15.FR.11: AND EV charging profile is within limits of CSMS ChargingSchedule CSMS responds with NotifyEVChargingScheduleResponse with status Accepted to Charging Station. Note: Already checked by Charging Station, but CSMS does its own check.
    Precondition: K15.FR.10 AND EV charging profile is within limits of CSMS ChargingSchedule
System under test: CSMS

Description:
    ISO15118-1 E1 AC Charging with load leveling based on High Level Communication, and E4 DC charging
    with load leveling based on High Level Communication.

Purpose:
    To verify if the CSMS is able to perform load leveling when it receives the EV charging needs from the
    Charging Station.

Before:
    Reusable State(s): State is Authorized AND EVConnectedPreSession

Main:
    Execute reusable state ISO15118SmartCharging
    (Steps: NotifyEVChargingNeeds -> SetChargingProfile -> NotifyEVChargingSchedule ->
     TransactionEvent ChargingStateChanged/Charging)
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
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
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
        self._received_set_charging_profile = asyncio.Event()
        self._set_charging_profile_data = None
        self._set_charging_profile_count = 0

    @on(Action.set_charging_profile)
    async def on_set_charging_profile(self, evse_id, charging_profile, **kwargs):
        logging.info(f"Received SetChargingProfileRequest: evse_id={evse_id}")
        self._set_charging_profile_data = {
            'evse_id': evse_id,
            'charging_profile': charging_profile,
        }
        self._set_charging_profile_count += 1
        self._received_set_charging_profile.set()
        return call_result.SetChargingProfile(
            status=ChargingProfileStatusEnumType.accepted
        )


@pytest.mark.asyncio
async def test_tc_k_53():
    """Charging with load leveling - Success (ISO15118SmartCharging)."""
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

    # Execute reusable state ISO15118SmartCharging

    # Step 1: Send NotifyEVChargingNeedsRequest
    notify_needs_payload = call.NotifyEVChargingNeeds(
        charging_needs={
            'requested_energy_transfer': EnergyTransferModeEnumType.ac_three_phase,
            'ac_charging_parameters': {
                'energy_amount': 50000,
                'ev_min_current': 6,
                'ev_max_current': 32,
                'ev_max_voltage': 230,
            },
        },
        evse_id=EVSE_ID,
        max_schedule_tuples=10,
    )
    # Step 2: CSMS responds with NotifyEVChargingNeedsResponse
    needs_response = await cp.call(notify_needs_payload)
    assert needs_response is not None
    assert needs_response.status in (
        NotifyEVChargingNeedsStatusEnumType.accepted,
        NotifyEVChargingNeedsStatusEnumType.processing,
    )

    # Step 3: Wait for CSMS to send SetChargingProfileRequest
    # Note: If NotifyEVChargingNeedsStatus was Processing, OCTT will wait 60 seconds
    await asyncio.wait_for(
        cp._received_set_charging_profile.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Step 4: CS responds with SetChargingProfileResponse (Accepted - handled by handler)
    assert cp._set_charging_profile_data is not None
    profile = cp._set_charging_profile_data['charging_profile']

    # Extract the charging schedule from the profile set by CSMS
    def get_field(d, snake, camel):
        v = d.get(snake)
        return v if v is not None else d.get(camel)

    schedules = get_field(profile, 'charging_schedule', 'chargingSchedule')
    schedule = schedules[0] if isinstance(schedules, list) else schedules

    # Step 5: Send NotifyEVChargingScheduleRequest with the schedule from step 3
    notify_schedule_payload = call.NotifyEVChargingSchedule(
        time_base=now_iso(),
        charging_schedule=schedule,
        evse_id=EVSE_ID,
    )
    # Step 6: CSMS responds with NotifyEVChargingScheduleResponse
    schedule_response = await cp.call(notify_schedule_payload)
    assert schedule_response is not None

    # Step 7: Send TransactionEventRequest (ChargingStateChanged, Charging)
    event = TransactionEvent(
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
    # Step 8: CSMS responds with TransactionEventResponse
    event_response = await cp.send_transaction_event_request(event)
    assert event_response is not None

    # Step 2 (main): Verify CSMS does NOT send an additional SetChargingProfileRequest
    # The CSMS must NOT initiate a renegotiate after starting the transaction, without cause.
    profile_count_before = cp._set_charging_profile_count
    try:
        cp._received_set_charging_profile.clear()
        await asyncio.wait_for(
            cp._received_set_charging_profile.wait(),
            timeout=5,
        )
        assert False, \
            "CSMS must NOT send an additional SetChargingProfileRequest without cause"
    except asyncio.TimeoutError:
        pass  # Expected - no additional SetChargingProfileRequest received

    assert cp._set_charging_profile_count == profile_count_before, \
        "CSMS must NOT send additional SetChargingProfileRequest after ISO15118SmartCharging"

    logging.info("TC_K_53 completed successfully")
    start_task.cancel()
    await ws.close()
