"""
TC_E_16 - Stop transaction options - Deauthorized - Invalid idToken
Use case: E06(S3) | Requirements: E06.FR.04, E01.FR.11, E01.FR.12
E06.FR.04: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse. The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS. See use case E05 - Start Transaction - Id not Accepted.
    Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse
E01.FR.11: The CSMS SHALL verify the validity of the identifier in TransactionEventRequest.
    Precondition: E01.FR.10
E01.FR.12: The CSMS SHALL send a TransactionEventResponse that includes in idTokenInfo an authorization status value and the groupIdToken if one exists for the idToken.
    Precondition: E01.FR.11
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that stops a transaction when the transaction
gets deauthorized via idTokenInfo.status=Invalid/Unknown in TransactionEventResponse.

Configuration:
    CSMS_ADDRESS        - WebSocket URL of the CSMS
    BASIC_AUTH_CP       - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD - Charge Point password
    INVALID_ID_TOKEN    - Invalid idToken value (CSMS should return Invalid/Unknown)
    INVALID_ID_TOKEN_TYPE - Invalid idToken type
    CONFIGURED_EVSE_ID  - EVSE id (default 1)
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
    ReasonEnumType as StoppedReasonType,
    AuthorizationStatusEnumType as AuthorizationStatusType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
INVALID_ID_TOKEN = os.environ['INVALID_ID_TOKEN']
INVALID_ID_TOKEN_TYPE = os.environ['INVALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_e_16(connection):
    """Stop transaction options - Deauthorized - Invalid idToken (E06.FR.04, E01.FR.11, E01.FR.12).
    E06.FR.04: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse. The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS. See use case E05 - Start Transaction - Id not Accepted.
        Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse
    E01.FR.11: The CSMS SHALL verify the validity of the identifier in TransactionEventRequest.
        Precondition: E01.FR.10
    E01.FR.12: The CSMS SHALL send a TransactionEventResponse that includes in idTokenInfo an authorization status value and the groupIdToken if one exists for the idToken.
        Precondition: E01.FR.11
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Step 1-2: TransactionEvent Started with invalid idToken
    # CSMS must respond with idTokenInfo.status = Invalid or Unknown
    started_event = TransactionEvent(
        event_type=TransactionEventType.started,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.authorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
        },
        id_token={
            'id_token': INVALID_ID_TOKEN,
            'type': INVALID_ID_TOKEN_TYPE,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    started_response = await cp.send_transaction_event_request(started_event)
    assert started_response is not None
    assert started_response.id_token_info is not None
    assert started_response.id_token_info.status in (
        AuthorizationStatusType.invalid,
        AuthorizationStatusType.unknown,
    )

    # Step 3-4: TransactionEvent Ended / Deauthorized / DeAuthorized
    end_event = TransactionEvent(
        event_type=TransactionEventType.ended,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.deauthorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'stopped_reason': StoppedReasonType.de_authorized,
        },
    )
    end_response = await cp.send_transaction_event_request(end_event)
    assert end_response is not None

    start_task.cancel()
