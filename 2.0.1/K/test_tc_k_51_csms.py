"""
TC_K_51 - Reset / release external charging limit - With ongoing transaction
Use case: K13 | Requirements: N/a
System under test: CSMS

Description:
    A charging schedule or charging limit can be removed by an external system on the Charging Station. An
    external control system sends a signal to release a previously imposed charging limit to a Charging
    Station. The Charging Station notifies the CSMS about this.

Before:
    Reusable State: EnergyTransferStarted

Main:
    1. The OCTT sends a ClearedChargingLimitRequest with chargingLimitSource EMS
    2. The CSMS responds with a ClearedChargingLimitResponse
    3. The OCTT sends a TransactionEventRequest with eventType Updated, triggerReason ChargingRateChanged
    4. The CSMS responds with a TransactionEventResponse
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201 import call
from ocpp.v201.call import TransactionEvent
from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    ChargingLimitSourceEnumType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started

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
async def test_tc_k_51():
    """Reset / release external charging limit - With ongoing transaction."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ws = await websockets.connect(uri=uri, subprotocols=['ocpp2.0.1'], extra_headers=headers)
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted
    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Before: Execute Reusable State EnergyTransferStarted
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Step 1-2: Send ClearedChargingLimitRequest
    payload = call.ClearedChargingLimit(
        charging_limit_source=ChargingLimitSourceEnumType.ems,
    )
    response = await cp.call(payload)
    assert response is not None

    # Step 3-4: Send TransactionEventRequest (Updated, ChargingRateChanged)
    event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.charging_rate_changed,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.charging,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    event_response = await cp.send_transaction_event_request(event)
    assert event_response is not None

    logging.info("TC_K_51 completed successfully")
    start_task.cancel()
    await ws.close()
