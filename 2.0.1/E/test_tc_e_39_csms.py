"""
TC_E_39 - Stop transaction options - Deauthorized - timeout
Use case: E03, E06 | Requirements: E03.FR.04, E03.FR.05, E06.FR.04
E03.FR.04: The field reservationId is only provided in the first TransactionEventRequest that occurs when the transaction has been authorized by the idToken for which a reservation existed in the charging station.
E03.FR.05: The stoppedReason must be provided in the TransactionEventRequest(eventType=Ended), unless the value is Local, in which case it may be omitted.
E06.FR.04: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse. The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS. See use case E05 - Start Transaction - Id not Accepted.
    Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that deauthorizes the transaction after the
EVConnectionTimeout has expired (EV driver authorized but EV not connected within timeout).

Before: Reusable State Authorized

Test sequence:
1. CS sends TransactionEvent Ended / EVConnectTimeout / Timeout
   (This step executes after EVConnectionTimeout expires)

Note: This test simulates the timeout behavior. In reality, the CS would wait for the configured
EVConnectionTimeout period before sending the Ended event.

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
    ReasonEnumType as StoppedReasonType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso
from reusable_states.authorized import authorized

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
async def test_tc_e_39(connection):
    """Stop transaction options - Deauthorized - timeout (E03.FR.04, E03.FR.05, E06.FR.04).
    E03.FR.04: The field reservationId is only provided in the first TransactionEventRequest that occurs when the transaction has been authorized by the idToken for which a reservation existed in the charging station.
    E03.FR.05: The stoppedReason must be provided in the TransactionEventRequest(eventType=Ended), unless the value is Local, in which case it may be omitted.
    E06.FR.04: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse. The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS. See use case E05 - Start Transaction - Id not Accepted.
        Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Before: Authorized
    await authorized(
        cp,
        id_token_id=VALID_ID_TOKEN,
        id_token_type=VALID_ID_TOKEN_TYPE,
        transaction_id=transaction_id,
        evse_id=EVSE_ID,
        connector_id=CONNECTOR_ID,
        ev_connected_pre_session=False,
    )

    # Step 1-2: TransactionEvent Ended / EVConnectTimeout / Timeout
    # Note: In reality, this would be sent after EVConnectionTimeout expires
    timeout_event = TransactionEvent(
        event_type=TransactionEventType.ended,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.ev_connect_timeout,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'stopped_reason': StoppedReasonType.timeout,
        },
    )
    response = await cp.send_transaction_event_request(timeout_event)
    assert response is not None

    start_task.cancel()
