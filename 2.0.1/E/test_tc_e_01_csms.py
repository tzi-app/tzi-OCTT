"""
TC_E_01 - Start transaction options - PowerPathClosed
Use case: E01(S5) | Requirement: E01.FR.05
E01.FR.05: TxStartPoint contains: PowerPathClosed AND The EV Driver is authorized AND The Charging Station has connection with the EV AND No transaction has started yet on this EVSE. The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType = Started) to the CSMS.
    Precondition: TxStartPoint contains: PowerPathClosed AND The EV Driver is authorized AND The Charging Station has connection with the EV AND No transaction has started yet on this EVSE
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that starts a transaction when the power path
has been closed (chargingState=SuspendedEVSE first, then Charging).

Configuration:
    CSMS_ADDRESS     - WebSocket URL of the CSMS (e.g. ws://localhost:8081)
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
from ocpp.v201.datatypes import ComponentType, VariableType, EventDataType
from ocpp.v201.enums import (
    ConnectorStatusEnumType as ConnectorStatusType,
    EventTriggerEnumType as EventTriggerType,
    EventNotificationEnumType as EventNotificationType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
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
async def test_tc_e_01(connection):
    """Start transaction options - PowerPathClosed (E01.FR.05).
    E01.FR.05: TxStartPoint contains: PowerPathClosed AND The EV Driver is authorized AND The Charging Station has connection with the EV AND No transaction has started yet on this EVSE. The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType = Started) to the CSMS.
        Precondition: TxStartPoint contains: PowerPathClosed AND The EV Driver is authorized AND The Charging Station has connection with the EV AND No transaction has started yet on this EVSE
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Step 1-2: Authorize
    authorize_response = await cp.send_authorization_request(
        id_token=VALID_ID_TOKEN, token_type=VALID_ID_TOKEN_TYPE
    )
    assert authorize_response is not None
    assert authorize_response.id_token_info.status == AuthorizationStatusType.accepted

    # Step 3-4: StatusNotification + NotifyEvent - connector Occupied
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

    # Step 5-6: TransactionEvent Started / ChargingStateChanged / SuspendedEVSE
    started_event = TransactionEvent(
        event_type=TransactionEventType.started,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.charging_state_changed,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.suspended_evse,
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

    # Step 7-8: TransactionEvent Updated / ChargingStateChanged / Charging
    charging_event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.charging_state_changed,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.charging,
        },
    )
    charging_response = await cp.send_transaction_event_request(charging_event)
    assert charging_response is not None

    start_task.cancel()
