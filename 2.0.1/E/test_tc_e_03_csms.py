"""
TC_E_03 - Local start transaction - Cable plugin first - Success
Use case: E02 | Requirement: E02.FR.02
E02.FR.02: The TransactionEventRequest(eventType=Started) must contain the meter values that have been configured in SampledDataCtrlr.TxStartedMeasurands.
    Precondition: E02.FR.01
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that starts a charging session when the EV
driver first connects the EV and EVSE, then authorizes.

Sequence: EVConnectedPreSession → Authorized → EnergyTransferStarted

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
async def test_tc_e_03(connection):
    """Local start transaction - Cable plugin first (E02.FR.02).
    E02.FR.02: The TransactionEventRequest(eventType=Started) must contain the meter values that have been configured in SampledDataCtrlr.TxStartedMeasurands.
        Precondition: E02.FR.01
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Before: EVConnectedPreSession
    status_response = await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusType.occupied,
    )
    assert status_response is not None

    pre_session_event_data = [EventDataType(
        trigger=EventTriggerType.delta,
        actual_value='Occupied',
        component=ComponentType(name='Connector'),
        variable=VariableType(name='AvailabilityState'),
        timestamp=now_iso(),
        event_id=EVSE_ID,
        event_notification_type=EventNotificationType.custom_monitor,
    )]
    pre_session_notify_response = await cp.send_notify_event(data=pre_session_event_data)
    assert pre_session_notify_response is not None

    pre_session_event = TransactionEvent(
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
    pre_session_response = await cp.send_transaction_event_request(pre_session_event)
    assert pre_session_response is not None

    # Step 1: Authorized (ev_connected_pre_session=True → eventType=Updated)
    await authorized(
        cp,
        id_token_id=VALID_ID_TOKEN,
        id_token_type=VALID_ID_TOKEN_TYPE,
        transaction_id=transaction_id,
        evse_id=EVSE_ID,
        connector_id=CONNECTOR_ID,
        ev_connected_pre_session=True,
    )

    # Step 2: EnergyTransferStarted (already connected, only part 2 applies)
    charging_event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.charging_state_changed,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.charging,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    charging_response = await cp.send_transaction_event_request(charging_event)
    assert charging_response is not None

    start_task.cancel()
