"""
TC_E_31 - Check Transaction status - Transaction with id ended - with message in queue
Use case: E14 | Requirements: E14.FR.03, E14.FR.04
E14.FR.03: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has stopped The Charging Station’s response SHALL have ongoingIndicator = false.
    Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has stopped
E14.FR.04: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It has transaction-related messages to be delivered about the transaction with that transactionId The Charging Station’s response SHALL have messagesInQueue = true.
    Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It has transaction-related messages to be delivered about the transaction with that transactionId
System under test: CSMS

Purpose: Verify the CSMS can request the status of queued TransactionEventRequest messages from a
specific transaction by sending GetTransactionStatusRequest with a transactionId. The CS responds
that there are messages queued belonging to an ended transaction with the requested id.

Before: Reusable State EnergyTransferStarted

Test sequence:
1. CS closes WebSocket connection
2. CS reconnects to CSMS
3. CS sends StatusNotificationRequest (Available)
4. CS sends TransactionEventRequest Ended (offline=true, seqNo skips 2 values)
5. CSMS sends GetTransactionStatusRequest with transactionId
6. CS responds with ongoingIndicator=false, messagesInQueue=true
7-8. CS sends 2 queued TransactionEventRequest Updated (offline=true, with skipped seqNo values)

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
from ocpp.v201.enums import (
    ConnectorStatusEnumType as ConnectorStatusType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
    ReasonEnumType as StoppedReasonType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context
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
async def test_tc_e_31():
    """Check Transaction status - ended with message in queue (E14.FR.03, E14.FR.04).
    E14.FR.03: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has stopped The Charging Station’s response SHALL have ongoingIndicator = false.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The transaction with that transactionId has stopped
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

        current_seq = cp.seq_no

        # Step 1: CS closes WebSocket connection
        start_task.cancel()
        await ws.close()

        # Wait before reconnecting
        await asyncio.sleep(TRANSACTION_DURATION)

        # Step 2: Reconnect to CSMS
        ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
        ws = await websockets.connect(
            uri=f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}',
            subprotocols=['ocpp2.0.1'],
            extra_headers=headers,
            ssl=ssl_ctx,
        )
        time.sleep(0.5)

        cp = TziChargePoint(BASIC_AUTH_CP, ws)
        cp.seq_no = current_seq  # Restore sequence number
        # Pre-configure response for GetTransactionStatus
        cp._get_transaction_status_ongoing_indicator = False
        cp._get_transaction_status_messages_in_queue = True
        start_task = asyncio.create_task(cp.start())

        # Drain CSMS-initiated messages after reconnection
        await cp.drain_post_boot()

        # Step 3-4: StatusNotificationRequest Available
        status_response = await cp.send_status_notification(connector_id=CONNECTOR_ID, status=ConnectorStatusType.available)
        assert status_response is not None

        # Step 5-6: TransactionEvent Ended (offline=true, seqNo skips 2 values)
        skipped_seq_1 = cp.next_seq_no()
        skipped_seq_2 = cp.next_seq_no()
        ended_seq = cp.next_seq_no()

        ended_event = TransactionEvent(
            event_type=TransactionEventType.ended,
            timestamp=now_iso(),
            trigger_reason=TriggerReasonType.ev_communication_lost,
            seq_no=ended_seq,
            transaction_info={
                'transaction_id': transaction_id,
                'charging_state': ChargingStateType.idle,
                'stopped_reason': StoppedReasonType.ev_disconnected,
            },
            offline=True,
        )
        response = await cp.send_transaction_event_request(ended_event)
        assert response is not None

        # Step 7: Wait for CSMS to send GetTransactionStatusRequest
        await asyncio.wait_for(
            cp._received_get_transaction_status.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )

        # Validate transactionId in request
        assert cp._get_transaction_status_data is not None
        assert cp._get_transaction_status_data['transaction_id'] == transaction_id

        # Step 9-10: Send first queued TransactionEventRequest (Updated, offline=true, first skipped seqNo)
        queued_event_1 = TransactionEvent(
            event_type=TransactionEventType.updated,
            timestamp=now_iso(),
            trigger_reason=TriggerReasonType.stop_authorized,
            seq_no=skipped_seq_1,
            transaction_info={'transaction_id': transaction_id},
            offline=True,
        )
        response = await cp.send_transaction_event_request(queued_event_1)
        assert response is not None

        # Step 11-12: Send second queued TransactionEventRequest (Updated, offline=true, second skipped seqNo)
        queued_event_2 = TransactionEvent(
            event_type=TransactionEventType.updated,
            timestamp=now_iso(),
            trigger_reason=TriggerReasonType.charging_state_changed,
            seq_no=skipped_seq_2,
            transaction_info={
                'transaction_id': transaction_id,
                'charging_state': ChargingStateType.ev_connected,
            },
            offline=True,
        )
        response = await cp.send_transaction_event_request(queued_event_2)
        assert response is not None

    except Exception as e:
        pytest.fail(f"Test failed: {e}")
    finally:
        start_task.cancel()
        await ws.close()
