"""
TC_K_37 - Remote start transaction with charging profile - Success
Use case: K05,F01 | Requirements: K05.FR.02,F01.FR.08,F01.FR.09,F01.FR.11
K05.FR.02: When receiving a GetChargingProfilesRequest, the Charging Station SHALL respond with GetChargingProfilesResponse and send ReportChargingProfilesRequest messages.
    Precondition: K05.FR.01
F01.FR.08: The CSMS MAY include a ChargingProfile in the RequestStartTransactionRequest.
F01.FR.09: F01.FR.08 AND The purpose of this ChargingProfile SHALL be set to TxProfile.
    Precondition: F01.FR.08
F01.FR.11: F01.FR.08 AND The transactionId in the ChargingProfile SHALL NOT be set.
    Precondition: F01.FR.08
System under test: CSMS

Description:
    The CSMS sets a TxProfile on a specific EVSE inside a RequestStartTransactionRequest message.

Purpose:
    To verify if the CSMS is able to set a TxProfile on a specific EVSE in a RequestStartTransactionRequest
    message.

Before:
    Reusable State(s): N/a

Main:
    1. The CSMS sends a RequestStartTransactionRequest
    2. The OCTT responds with a RequestStartTransactionResponse with status Accepted
    3. The OCTT sends a TransactionEventRequest with triggerReason RemoteStart,
       transactionInfo.remoteStartId is present.
    4. The CSMS responds with a TransactionEventResponse

Tool validations:
    * Step 1: Message RequestStartTransactionRequest
      - idToken.idToken <Configured valid_idtoken_idtoken>
      - idToken.type <Configured valid_idtoken_type>
      - idToken.idToken <Configured valid idToken>
      - idToken.type <Configured valid idToken type>
      - evseId <Configured evseId>
      - chargingProfile contains:
      - chargingProfile.chargingProfilePurpose is TxProfile
      - chargingProfile.transactionId is omitted
      - chargingProfile.chargingProfileKind is Relative OR Absolute
      If chargingProfileKind is Relative then chargingSchedule.startSchedule must be omitted.
      If chargingProfileKind is Absolute then chargingSchedule.startSchedule must NOT be omitted.
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.call import TransactionEvent
from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingProfilePurposeEnumType,
    ChargingProfileKindEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_k_37():
    """Remote start transaction with charging profile - Success."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1-2: Wait for CSMS to send RequestStartTransactionRequest
    await asyncio.wait_for(
        cp._received_request_start_transaction.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._request_start_transaction_data is not None
    req_data = cp._request_start_transaction_data

    # Validate idToken
    id_token = req_data['id_token']
    if isinstance(id_token, dict):
        assert id_token.get('id_token') == VALID_ID_TOKEN, \
            f"Expected idToken={VALID_ID_TOKEN}, got {id_token.get('id_token')}"
        assert id_token.get('type') == VALID_ID_TOKEN_TYPE, \
            f"Expected idToken.type={VALID_ID_TOKEN_TYPE}, got {id_token.get('type')}"

    # Validate evseId
    assert req_data['evse_id'] == EVSE_ID, \
        f"Expected evseId={EVSE_ID}, got {req_data['evse_id']}"

    # Validate chargingProfile
    charging_profile = req_data['charging_profile']
    assert charging_profile is not None, "chargingProfile must be present"

    purpose = charging_profile.get('charging_profile_purpose') or charging_profile.get('chargingProfilePurpose')
    assert purpose in ('TxProfile', ChargingProfilePurposeEnumType.tx_profile), \
        f"Expected purpose=TxProfile, got {purpose}"

    tx_id = charging_profile.get('transaction_id') or charging_profile.get('transactionId')
    assert tx_id is None, f"Expected transactionId to be omitted, got {tx_id}"

    kind = charging_profile.get('charging_profile_kind') or charging_profile.get('chargingProfileKind')
    assert kind in ('Relative', 'Absolute', ChargingProfileKindEnumType.relative, ChargingProfileKindEnumType.absolute), \
        f"Expected kind=Relative or Absolute, got {kind}"

    # Conditional startSchedule validation based on chargingProfileKind
    schedules = charging_profile.get('charging_schedule') or charging_profile.get('chargingSchedule')
    if schedules:
        schedule = schedules[0] if isinstance(schedules, list) else schedules
        start_schedule = schedule.get('start_schedule') or schedule.get('startSchedule')
        if kind in ('Relative', ChargingProfileKindEnumType.relative):
            assert start_schedule is None, \
                f"Expected startSchedule to be omitted for Relative kind, got {start_schedule}"
        elif kind in ('Absolute', ChargingProfileKindEnumType.absolute):
            assert start_schedule is not None, \
                "Expected startSchedule to be present for Absolute kind"

    remote_start_id = req_data['remote_start_id']
    assert remote_start_id is not None

    # Step 3-4: CS sends TransactionEventRequest (RemoteStart)
    event = TransactionEvent(
        event_type=TransactionEventType.started,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.remote_start,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'remote_start_id': remote_start_id,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    event_response = await cp.send_transaction_event_request(event)
    assert event_response is not None

    logging.info("TC_K_37 completed successfully")
    start_task.cancel()
    await ws.close()
