"""
TC_E_09 - Start transaction options - EVConnected
Use case: E01(S2) | Requirement: E01.FR.02
E01.FR.02: TxStartPoint contains: EVConnected AND The Charging Station has a connection with the EV AND No transaction has started yet on this EVSE The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType = Started) to the CSMS.
    Precondition: TxStartPoint contains: EVConnected AND The Charging Station has a connection with the EV AND No transaction has started yet on this EVSE
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that starts a transaction when the EV and
EVSE are connected (TxStartPoint = EVConnected).

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
from ocpp.v201.datatypes import ComponentType, VariableType, EventDataType
from ocpp.v201.enums import (
    ConnectorStatusEnumType as ConnectorStatusType,
    EventTriggerEnumType as EventTriggerType,
    EventNotificationEnumType as EventNotificationType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
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
async def test_tc_e_09(connection):
    """Start transaction options - EVConnected (E01.FR.02).
    E01.FR.02: TxStartPoint contains: EVConnected AND The Charging Station has a connection with the EV AND No transaction has started yet on this EVSE The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType = Started) to the CSMS.
        Precondition: TxStartPoint contains: EVConnected AND The Charging Station has a connection with the EV AND No transaction has started yet on this EVSE
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Step 1-2: StatusNotification + NotifyEvent - connector Occupied
    status_response = await cp.send_status_notification(connector_id=CONNECTOR_ID, status=ConnectorStatusType.occupied)
    assert status_response is not None

    event_data = [EventDataType(
        trigger=EventTriggerType.delta,
        actual_value='Occupied',
        component=ComponentType(name='Connector'),
        variable=VariableType(name='AvailabilityState'),
        timestamp=now_iso(),
        event_id=EVSE_ID,
        event_notification_type=EventNotificationType.custom_monitor,
    )]
    notify_response = await cp.send_notify_event(data=event_data)
    assert notify_response is not None

    # Step 3-4: TransactionEvent Started / CablePluggedIn / EVConnected
    started_event = TransactionEvent(
        event_type=TransactionEventType.started,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.cable_plugged_in,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.ev_connected,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    started_response = await cp.send_transaction_event_request(started_event)
    assert started_response is not None

    start_task.cancel()
