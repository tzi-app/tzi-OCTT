"""
TC_F_04 - Remote start transaction - Remote start first - Cable plugin timeout
Use case: F02, E03 | Requirements: E03.FR.04, E03.FR.05
E03.FR.04: The field reservationId is only provided in the first TransactionEventRequest that occurs when the transaction has been authorized by the idToken for which a reservation existed in the charging station.
E03.FR.05: The stoppedReason must be provided in the TransactionEventRequest(eventType=Ended), unless the value is Local, in which case it may be omitted.
System under test: CSMS

Description:
    OCPP 2.x.x allows an EV driver to either first wait for/trigger a RequestStartTransactionRequest OR
    connect the EV and EVSE. Both sequences will result in being able to charge.

Purpose:
    To verify if the CSMS is able to handle a Charging Station that deauthorizes the transaction after the
    EVConnectionTimeout has been reached.

Main:
    Manual Action: Trigger the CSMS to request the CS to start a transaction.
    1. CSMS sends RequestStartTransactionRequest
    2. CS responds with RequestStartTransactionResponse (status=Accepted, transactionId omitted)
    3. CS sends TransactionEventRequest (triggerReason=RemoteStart, remoteStartId=<generated>, eventType=Started)
    4. CSMS responds with TransactionEventResponse
    5. CS sends TransactionEventRequest (triggerReason=EVConnectTimeout, eventType=Updated)
       Note: This step will be executed after the <Configured Transaction Duration> has been reached.
    6. CSMS responds with TransactionEventResponse

Tool validations:
    * Step 1: RequestStartTransactionRequest
      - idToken.idToken <Configured valid_idtoken_idtoken>
      - idToken.type <Configured valid_idtoken_type>

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    VALID_ID_TOKEN            - Valid idToken value
    VALID_ID_TOKEN_TYPE       - Valid idToken type
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
    TRANSACTION_DURATION      - Seconds to wait before EVConnectTimeout (default 5)
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
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


@pytest.mark.asyncio
async def test_tc_f_04():
    """Remote start transaction - Remote start first - Cable plugin timeout."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available, evse_id=EVSE_ID)

    # Step 1-2: Wait for CSMS to send RequestStartTransactionRequest
    # Manual action: Trigger the CSMS to request the CS to start a transaction
    await asyncio.wait_for(
        cp._received_request_start_transaction.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate Step 1: RequestStartTransactionRequest content
    assert cp._request_start_transaction_data is not None
    req_data = cp._request_start_transaction_data
    id_token = req_data['id_token']
    if isinstance(id_token, dict):
        assert id_token.get('id_token') == VALID_ID_TOKEN, \
            f"Expected idToken={VALID_ID_TOKEN}, got {id_token.get('id_token')}"
        assert id_token.get('type') == VALID_ID_TOKEN_TYPE, \
            f"Expected idToken.type={VALID_ID_TOKEN_TYPE}, got {id_token.get('type')}"

    remote_start_id = req_data['remote_start_id']
    assert remote_start_id is not None

    # Step 3-4: CS sends TransactionEventRequest (Started, RemoteStart)
    start_event = TransactionEvent(
        event_type=TransactionEventType.started,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.remote_start,
        seq_no=0,
        transaction_info={
            'transaction_id': transaction_id,
            'remote_start_id': remote_start_id,
        },
        id_token={
            'id_token': VALID_ID_TOKEN,
            'type': VALID_ID_TOKEN_TYPE,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    start_response = await cp.send_transaction_event_request(start_event)
    assert start_response is not None

    # Wait for EVConnectionTimeout
    logging.info(f"Waiting {TRANSACTION_DURATION}s for EVConnectionTimeout...")
    await asyncio.sleep(TRANSACTION_DURATION)

    # Step 5-6: CS sends TransactionEventRequest (Updated, EVConnectTimeout)
    timeout_event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.ev_connect_timeout,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
        },
    )
    timeout_response = await cp.send_transaction_event_request(timeout_event)
    assert timeout_response is not None

    logging.info("TC_F_04 completed successfully")
    start_task.cancel()
    await ws.close()
