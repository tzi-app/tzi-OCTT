"""
TC_E_53 - Reset Sequence Number - CSMS accepting seqNo = 0 at start of transaction
Use case: E01 | Requirement: E01.FR.07
E01.FR.07: When a TransactionEventRequest has to be created The Charging Station SHALL set the message’s seqNo field as specified in Sequence Number Generation.
    Precondition: When a TransactionEventRequest has to be created
System under test: CSMS

Description: OCPP 2.0.1 Edition 2 recommends that seqNo starts at 0 for every transaction. CSMS must
therefore be robust to a seqNo that is not continuously increasing, but that restarts for new
transactions. Since a TransactionEventRequest cannot be rejected, this can only be detected by
either the complete absence of a TransactionEventResponse from CSMS or an otherwise misbehaving CSMS.

Purpose: To verify if the CSMS accepts that a new transaction starts with a seqNo = 0.

Test sequence:
1. Execute Reusable State EnergyTransferStarted (seqNo starts at 0)
2. Execute Reusable State EVDisconnected
3. Execute Reusable State EnergyTransferStarted (seqNo starts at 0 again)
4. Execute Reusable State EVDisconnected

Tool validations:
* Step 1: CSMS accepts TransactionEventRequest with eventType=Started and seqNo=0
* Step 3: CSMS accepts TransactionEventRequest with eventType=Started and seqNo=0

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

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.stop_authorized import stop_authorized
from reusable_states.ev_connected_post_session import ev_connected_post_session
from reusable_states.ev_disconnected import ev_disconnected

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
async def test_tc_e_53(connection):
    """Reset Sequence Number - CSMS accepting seqNo = 0 (E01.FR.07).
    E01.FR.07: When a TransactionEventRequest has to be created The Charging Station SHALL set the message’s seqNo field as specified in Sequence Number Generation.
        Precondition: When a TransactionEventRequest has to be created
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # --- Transaction 1 ---
    transaction_id_1 = generate_transaction_id()

    # Reset seqNo so first TransactionEventRequest (Started) uses seqNo=0
    # next_seq_no() pre-increments, so setting to -1 makes first call return 0
    cp.seq_no = -1

    # Step 1: EnergyTransferStarted (Authorized -> EnergyTransferStarted)
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id_1, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id_1)

    # Step 2: EVDisconnected (StopAuthorized -> EVConnectedPostSession -> EVDisconnected)
    await stop_authorized(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                          transaction_id=transaction_id_1)
    await ev_connected_post_session(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                    transaction_id=transaction_id_1)
    await ev_disconnected(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                          transaction_id=transaction_id_1)

    # --- Transaction 2 ---
    transaction_id_2 = generate_transaction_id()

    # Reset seqNo again so new transaction starts with seqNo=0
    cp.seq_no = -1

    # Step 3: EnergyTransferStarted (Authorized -> EnergyTransferStarted)
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id_2, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id_2)

    # Step 4: EVDisconnected (StopAuthorized -> EVConnectedPostSession -> EVDisconnected)
    await stop_authorized(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                          transaction_id=transaction_id_2)
    await ev_connected_post_session(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                    transaction_id=transaction_id_2)
    await ev_disconnected(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                          transaction_id=transaction_id_2)

    start_task.cancel()
