"""
TC_F_03 - Remote start transaction - Remote start first - AuthorizeRemoteStart is false
Use case: F02 | Requirements: F02.FR.01, F01.FR.02
F02.FR.01: The remoteStartId must be sent in the next TransactionEventRequest after the RequestStartTransactionRequest with the same remoteStartId.
    Precondition: When a transaction is started as a result of a RequestStartTransactionRequest.
F01.FR.02: Charging Station receives a RequestStartTransactionRequest AND ( AuthorizeRemoteStart = false OR idToken.type is Central or NoAuthorization ) The Charging Station SHALL allow energy transfer for the IdToken given in RequestStartTransactionRequest message without
    Precondition: Charging Station receives a RequestStartTransactionRequest AND (AuthorizeRemoteStart = false OR idToken.type is Central or NoAuthorization)
System under test: CSMS

Description:
    OCPP 2.x.x allows an EV driver to either first wait for/trigger a RequestStartTransactionRequest OR
    connect the EV and EVSE. Both sequences will result in being able to charge.

Purpose:
    To verify if the CSMS is able to handle a Charging Station that starts a charging session when the
    Charging Station receives a RequestStartTransactionRequest message (while AuthorizeRemoteStart is false),
    before the EV driver connects the EV and EVSE (within the connectionTimeout). The Charging station does
    NOT have to authorize beforehand like a local action to start a transaction.

Main:
    Manual Action: Trigger the CSMS to request the CS to start a transaction.
    1. CSMS sends RequestStartTransactionRequest
    2. CS responds with RequestStartTransactionResponse (status=Accepted, transactionId omitted)
    3. CS sends TransactionEventRequest (triggerReason=RemoteStart, remoteStartId=<generated>, eventType=Started)
    4. CSMS responds with TransactionEventResponse
    5. Execute Reusable State EnergyTransferStarted (Authorized, _EVConnected=false)

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
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context
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
async def test_tc_f_03():
    """Remote start transaction - Remote start first - AuthorizeRemoteStart is false."""
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

    # Step 3-4: CS sends TransactionEventRequest (Started, RemoteStart) - no AuthorizeRequest
    event = TransactionEvent(
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
    event_response = await cp.send_transaction_event_request(event)
    assert event_response is not None

    # Step 5: Execute Reusable State EnergyTransferStarted (Authorized, _EVConnected=false)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    logging.info("TC_F_03 completed successfully")
    start_task.cancel()
    await ws.close()
