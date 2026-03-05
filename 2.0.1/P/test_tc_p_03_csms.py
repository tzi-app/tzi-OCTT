"""
TC_P_03 - CustomData - Receive custom data
Use case: N/a | Requirements: N/a
System under test: CSMS

Description:
    Checks if the CSMS is able to receive custom data.

Purpose:
    To verify whether the CSMS is able to handle receiving custom data.

Main:
    1. OCTT sends StatusNotificationRequest with customData
    2. CSMS responds with StatusNotificationResponse
    3. OCTT sends TransactionEventRequest with customData and
       transactionInfo.customData
    4. CSMS responds with TransactionEventResponse

Tool validations:
    * N/a

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.call import StatusNotification, TransactionEvent
from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])

CUSTOM_DATA = {
    'vendor_id': 'tzi.app',
    'custom_key': 'custom_value',
}


@pytest.mark.asyncio
async def test_tc_p_03():
    """CustomData - Receive custom data."""
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

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Steps 1-2: Send StatusNotificationRequest with customData
    status_payload = StatusNotification(
        timestamp=now_iso(),
        connector_id=CONNECTOR_ID,
        evse_id=EVSE_ID,
        connector_status=ConnectorStatusEnumType.available,
        custom_data=CUSTOM_DATA,
    )
    status_response = await cp.call(status_payload)
    assert status_response is not None
    logging.info("Step 1-2: StatusNotificationRequest with customData sent successfully")

    # Steps 3-4: Send TransactionEventRequest with customData and transactionInfo.customData
    transaction_id = generate_transaction_id()
    tx_event_payload = TransactionEvent(
        event_type=TransactionEventType.started,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.authorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.ev_connected,
            'custom_data': CUSTOM_DATA,
        },
        custom_data=CUSTOM_DATA,
    )
    tx_response = await cp.send_transaction_event_request(tx_event_payload)
    assert tx_response is not None
    logging.info("Step 3-4: TransactionEventRequest with customData sent successfully")

    logging.info("TC_P_03 completed successfully")
    start_task.cancel()
    await ws.close()
