"""
TC_E_29 - Check Transaction status - Transaction with id ongoing - with message in queue
Use case: E14 | Requirements: E14.FR.02, E14.FR.04
E14.FR.02: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has not stopped yet The Charging Station’s response SHALL have ongoingIndicator = true. E. Transactions
    Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has not stopped yet
E14.FR.04: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It has transaction-related messages to be delivered about the transaction with that transactionId The Charging Station’s response SHALL have messagesInQueue = true.
    Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It has transaction-related messages to be delivered about the transaction with that transactionId
System under test: CSMS

Purpose: Verify the CSMS can request the status of queued TransactionEventRequest messages from a
specific transaction by sending GetTransactionStatusRequest with a transactionId. The CS responds
that there are messages queued belonging to the ongoing transaction with the requested id.

Before: Reusable State EnergyTransferStarted

Test sequence:
1. CS closes WebSocket connection
2. CS waits TRANSACTION_DURATION seconds (simulating queued messages), then reconnects
3. CSMS sends GetTransactionStatusRequest with transactionId
4. CS responds with ongoingIndicator=true, messagesInQueue=true
5. CS sends queued TransactionEventRequest with offline=true

Configuration:
    CSMS_ADDRESS     - WebSocket URL of the CSMS
    BASIC_AUTH_CP    - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD - Charge Point password
    VALID_ID_TOKEN   - Valid idToken value
    VALID_ID_TOKEN_TYPE - Valid idToken type
    CONFIGURED_EVSE_ID   - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID - Connector id (default 1)
    TRANSACTION_DURATION - Seconds to wait while offline (default 5)
    CSMS_ACTION_TIMEOUT - Seconds to wait for CSMS message (default 30)
"""
import asyncio
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.call import TransactionEvent
from ocpp.v201.datatypes import MeterValueType, SampledValueType
from ocpp.v201.enums import (
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context
from trigger import send_call
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_e_29():
    """Check Transaction status - ongoing with message in queue (E14.FR.02, E14.FR.04).
    E14.FR.02: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has not stopped yet The Charging Station’s response SHALL have ongoingIndicator = true. E. Transactions
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has not stopped yet
    E14.FR.04: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It has transaction-related messages to be delivered about the transaction with that transactionId The Charging Station’s response SHALL have messagesInQueue = true.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It has transaction-related messages to be delivered about the transaction with that transactionId
    """
    # This test manages its own WebSocket because it disconnects and reconnects
    # mid-test to simulate offline queued messages. The conftest fixture cannot handle this.
    headers = get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD)
    ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
    ws = await websockets.connect(
        uri=f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}',
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = TziChargePoint(BASIC_AUTH_CP, ws)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    try:
        # Before: EnergyTransferStarted
        await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                         transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
        await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                      transaction_id=transaction_id)

        # Step 1: CS closes WebSocket connection
        start_task.cancel()
        await ws.close()

        # Step 2: Wait TRANSACTION_DURATION seconds, then reconnect
        await asyncio.sleep(TRANSACTION_DURATION)

        ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
        ws = await websockets.connect(
            uri=f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}',
            subprotocols=['ocpp2.0.1'],
            extra_headers=headers,
            ssl=ssl_ctx,
        )
        time.sleep(0.5)

        cp = TziChargePoint(BASIC_AUTH_CP, ws)
        # Pre-configure response for GetTransactionStatus
        cp._get_transaction_status_ongoing_indicator = True
        cp._get_transaction_status_messages_in_queue = True
        start_task = asyncio.create_task(cp.start())

        # Drain CSMS-initiated messages after reconnection (stale transaction checks, etc.)
        await cp.drain_post_boot()

        # Step 3: Trigger CSMS to send GetTransactionStatusRequest
        async def trigger_get_status():
            await send_call(BASIC_AUTH_CP, "GetTransactionStatus",
                            {"transactionId": transaction_id})

        trigger_task = asyncio.create_task(trigger_get_status())

        await asyncio.wait_for(
            cp._received_get_transaction_status.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )
        trigger_task.cancel()

        # Step 4: Validate transactionId in request
        assert cp._get_transaction_status_data is not None
        assert cp._get_transaction_status_data['transaction_id'] == transaction_id

        # Step 5-6: CS sends queued TransactionEventRequest with offline=true
        meter_value = MeterValueType(
            timestamp=now_iso(),
            sampled_value=[SampledValueType(value=1.5)],
        )
        queued_event = TransactionEvent(
            event_type=TransactionEventType.updated,
            timestamp=now_iso(),
            trigger_reason=TriggerReasonType.meter_value_periodic,
            seq_no=cp.next_seq_no(),
            transaction_info={'transaction_id': transaction_id},
            meter_value=[meter_value],
            offline=True,
        )
        response = await cp.send_transaction_event_request(queued_event)
        assert response is not None

    except Exception as e:
        pytest.fail(f"Test failed: {e}")
    finally:
        start_task.cancel()
        await ws.close()
