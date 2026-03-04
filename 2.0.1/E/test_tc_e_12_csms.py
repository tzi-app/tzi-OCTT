"""
TC_E_12 - Start transaction options - ParkingBayOccupied
Use case: E01(S1) | Requirement: E01.FR.01
E01.FR.01: TxStartPoint contains: ParkingBayOccupancy AND Parking Bay Detector detects an "EV" AND No transaction has started yet The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType = Started) to the CSMS.
    Precondition: TxStartPoint contains: ParkingBayOccupancy AND Parking Bay Detector detects an "EV" AND No transaction has started yet
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that starts a transaction when the parking
bay is occupied (EV detected by sensor, TxStartPoint = ParkingBayOccupancy).

Configuration:
    CSMS_ADDRESS     - WebSocket URL of the CSMS
    BASIC_AUTH_CP    - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD - Charge Point password
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
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_e_12(connection):
    """Start transaction options - ParkingBayOccupied (E01.FR.01).
    E01.FR.01: TxStartPoint contains: ParkingBayOccupancy AND Parking Bay Detector detects an "EV" AND No transaction has started yet The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType = Started) to the CSMS.
        Precondition: TxStartPoint contains: ParkingBayOccupancy AND Parking Bay Detector detects an "EV" AND No transaction has started yet
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Step 1-2: TransactionEvent Started / EVDetected
    started_event = TransactionEvent(
        event_type=TransactionEventType.started,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.ev_detected,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
        },
    )
    started_response = await cp.send_transaction_event_request(started_event)
    assert started_response is not None

    start_task.cancel()
