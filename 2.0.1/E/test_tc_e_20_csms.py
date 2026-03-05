"""
TC_E_20 - Stop transaction options - EVDisconnected - EV side (IEC 61851-1)
Use case: E06(S2), E10 | Requirement: E06.FR.02
E06.FR.02: TxStopPoint contains: EVConnected AND Connection between Charging Station and EV is lost. The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS.
    Precondition: TxStopPoint contains: EVConnected AND Connection between Charging Station and EV is lost.
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that stops a transaction when the EV and
EVSE are disconnected at the EV side (able to charge IEC 61851-1 EV).

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

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.energy_transfer_suspended import energy_transfer_suspended
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
async def test_tc_e_20(connection):
    """Stop transaction options - EVDisconnected - EV side IEC 61851-1 (E06.FR.02).
    E06.FR.02: TxStopPoint contains: EVConnected AND Connection between Charging Station and EV is lost. The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS.
        Precondition: TxStopPoint contains: EVConnected AND Connection between Charging Station and EV is lost.
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

    # Step 1: EVDisconnected
    await ev_disconnected(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                           transaction_id=transaction_id)

    start_task.cancel()
