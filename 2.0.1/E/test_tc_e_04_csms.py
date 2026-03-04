"""
TC_E_04 - Local start transaction - Authorization first - Success
Use case: E03 | Requirement: E03.FR.02
E03.FR.02: The field idToken is provided once in the TransactionEventRequest that occurs when the authorization of the transaction has been ended.
    Precondition: E03.FR.01
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that starts a charging session when the EV
driver first presents identification, then connects the EV and EVSE.

Sequence: Authorized → EnergyTransferStarted

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
async def test_tc_e_04(connection):
    """Local start transaction - Authorization first (E03.FR.02).
    E03.FR.02: The field idToken is provided once in the TransactionEventRequest that occurs when the authorization of the transaction has been ended.
        Precondition: E03.FR.01
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Step 1: Authorized (no prior ev connection → eventType=Started)
    await authorized(
        cp,
        id_token_id=VALID_ID_TOKEN,
        id_token_type=VALID_ID_TOKEN_TYPE,
        transaction_id=transaction_id,
        evse_id=EVSE_ID,
        connector_id=CONNECTOR_ID,
        ev_connected_pre_session=False,
    )

    # Step 2: EnergyTransferStarted
    await energy_transfer_started(
        cp,
        evse_id=EVSE_ID,
        connector_id=CONNECTOR_ID,
        transaction_id=transaction_id,
    )

    start_task.cancel()
