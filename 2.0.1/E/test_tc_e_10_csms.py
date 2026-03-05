"""
TC_E_10 - Start transaction options - Authorized - Local
Use case: E01(S3) | Requirement: E01.FR.03
E01.FR.03: TxStartPoint contains: Authorized AND The EV Driver is authorized AND No transaction has started yet. The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType = Started) to the CSMS.
    Precondition: TxStartPoint contains: Authorized AND The EV Driver is authorized AND No transaction has started yet
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that starts a transaction when the EV driver
is locally authorized (TxStartPoint = Authorized).

Configuration:
    CSMS_ADDRESS     - WebSocket URL of the CSMS
    BASIC_AUTH_CP    - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD - Charge Point password
    VALID_ID_TOKEN   - Valid idToken value
    VALID_ID_TOKEN_TYPE - Valid idToken type
    CONFIGURED_EVSE_ID   - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID - Connector id (default 1)
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.call import TransactionEvent
from ocpp.v201.enums import (
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    AuthorizationStatusEnumType as AuthorizationStatusType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_e_10(connection):
    """Start transaction options - Authorized - Local (E01.FR.03).
    E01.FR.03: TxStartPoint contains: Authorized AND The EV Driver is authorized AND No transaction has started yet. The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType = Started) to the CSMS.
        Precondition: TxStartPoint contains: Authorized AND The EV Driver is authorized AND No transaction has started yet
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Step 1-2: AuthorizeRequest
    authorize_response = await cp.send_authorization_request(
        id_token=VALID_ID_TOKEN, token_type=VALID_ID_TOKEN_TYPE
    )
    assert authorize_response is not None
    assert authorize_response.id_token_info.status == AuthorizationStatusType.accepted

    # Step 3-4: TransactionEvent Started / Authorized
    started_event = TransactionEvent(
        event_type=TransactionEventType.started,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.authorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
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
    started_response = await cp.send_transaction_event_request(started_event)
    assert started_response is not None
    if started_response.id_token_info is not None:
        assert started_response.id_token_info.status == AuthorizationStatusType.accepted

    start_task.cancel()
