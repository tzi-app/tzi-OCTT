"""
TC_F_13 - Trigger message - TransactionEvent - Specific EVSE
Use case: F06 | Requirements: F06.FR.01, F06.FR.02
F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to receive.
F06.FR.02: The requested message SHALL be leading. If the specified evseId is not relevant to the message, it SHALL be ignored. In such cases the requested message SHALL still be sent.
    Precondition: F06.FR.01. For every such requested message.
System under test: CSMS

Description:
    The CSMS can request a Charging Station to send Charging Station-initiated messages. In the request
    the CSMS indicates which message it wishes to receive.

Purpose:
    To verify if the CSMS is able to trigger the Charging Station to send a TransactionEventRequest for
    a specific EVSE, using a TriggerMessageRequest.

Before:
    Reusable State: EnergyTransferStarted

Main:
    1. CSMS sends TriggerMessageRequest (requestedMessage=TransactionEvent, evse.id=<configured>)
    2. CS responds with TriggerMessageResponse (status=Accepted)
    3. CS sends TransactionEventRequest (evse.id=<configured>, triggerReason=Trigger,
       transactionInfo.chargingState=Charging, meterValue present,
       meterValue[0].sampledValue.context=Trigger)
    4. CSMS responds with TransactionEventResponse

Tool validations:
    * Step 1: TriggerMessageRequest
      - requestedMessage must be TransactionEvent
      - evse.id must be <Configured evseId>

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    VALID_ID_TOKEN            - Valid idToken value
    VALID_ID_TOKEN_TYPE       - Valid idToken type
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
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
    MessageTriggerEnumType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context
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
async def test_tc_f_13():
    """Trigger message - TransactionEvent - Specific EVSE."""
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

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available, evse_id=EVSE_ID)

    # Before: EnergyTransferStarted
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Step 1-2: Wait for CSMS to send TriggerMessageRequest
    await asyncio.wait_for(
        cp._received_trigger_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate Step 1: TriggerMessageRequest content
    assert cp._trigger_message_data == MessageTriggerEnumType.transaction_event or \
           cp._trigger_message_data == 'TransactionEvent', \
        f"Expected requestedMessage=TransactionEvent, got {cp._trigger_message_data}"

    assert cp._trigger_message_evse is not None, "Expected evse to be present"
    evse = cp._trigger_message_evse
    if isinstance(evse, dict):
        assert evse.get('id') == EVSE_ID, \
            f"Expected evse.id={EVSE_ID}, got {evse.get('id')}"

    # Step 3-4: CS sends TransactionEventRequest with Trigger reason
    event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.trigger,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.charging,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
        meter_value=[{
            'timestamp': now_iso(),
            'sampled_value': [{'value': 0.0, 'context': 'Trigger'}],
        }],
    )
    event_response = await cp.send_transaction_event_request(event)
    assert event_response is not None

    logging.info("TC_F_13 completed successfully")
    start_task.cancel()
    await ws.close()
