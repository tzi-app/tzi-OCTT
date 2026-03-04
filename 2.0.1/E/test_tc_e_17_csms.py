"""
TC_E_17 - Stop transaction options - Deauthorized - EV side disconnect
Use case: E06(S3) | Requirement: E06.FR.04
E06.FR.04: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse. The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS. See use case E05 - Start Transaction - Id not Accepted.
    Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that stops a transaction when the transaction
gets deauthorized due to EV side connection loss.

Before: Reusable State EnergyTransferSuspended

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
    ChargingStateEnumType as ChargingStateType,
    ReasonEnumType as StoppedReasonType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.energy_transfer_suspended import energy_transfer_suspended

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
async def test_tc_e_17(connection):
    """Stop transaction options - Deauthorized - EV side disconnect (E06.FR.04).
    E06.FR.04: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse. The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS. See use case E05 - Start Transaction - Id not Accepted.
        Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a TransactionEventResponse
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Before: EnergyTransferSuspended
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)
    await energy_transfer_suspended(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                     transaction_id=transaction_id)

    # Step 1-2: TransactionEvent Ended / EVCommunicationLost / Idle / EVDisconnected
    end_event = TransactionEvent(
        event_type=TransactionEventType.ended,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.ev_communication_lost,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.idle,
            'stopped_reason': StoppedReasonType.ev_disconnected,
        },
    )
    end_response = await cp.send_transaction_event_request(end_event)
    assert end_response is not None

    start_task.cancel()
