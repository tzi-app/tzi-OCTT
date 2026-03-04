"""
TC_E_26 - Disconnect cable on EV-side - Suspend transaction
Use case: E10 | Requirement: E10.FR.01
E10.FR.01: If StopTxOnEVSideDisconnect = false AND Cable not permanently attached The Connector SHALL remain locked at the Charging Station until the EV Driver presents the IdToken.
    Precondition: If StopTxOnEVSideDisconnect = false AND Cable not permanently attached
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that suspends the transaction when the EV
and EVSE are disconnected at the EV side AND restarts energy transfer after reconnecting.

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
async def test_tc_e_26(connection):
    """Disconnect cable on EV-side - Suspend transaction (E10.FR.01).
    E10.FR.01: If StopTxOnEVSideDisconnect = false AND Cable not permanently attached The Connector SHALL remain locked at the Charging Station until the EV Driver presents the IdToken.
        Precondition: If StopTxOnEVSideDisconnect = false AND Cable not permanently attached
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

    # Step 1-2: TransactionEvent Updated / EVCommunicationLost / Idle
    comm_lost_event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.ev_communication_lost,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.idle,
        },
    )
    response = await cp.send_transaction_event_request(comm_lost_event)
    assert response is not None

    # Step 3-4: StatusNotification Available + NotifyEvent
    status_response = await cp.send_status_notification(connector_id=CONNECTOR_ID, status=ConnectorStatusType.available)
    assert status_response is not None

    event_data = [EventDataType(
        trigger=EventTriggerType.delta,
        actual_value='Available',
        component=ComponentType(name='Connector', evse={'id': EVSE_ID, 'connectorId': CONNECTOR_ID}),
        variable=VariableType(name='AvailabilityState'),
        timestamp=now_iso(),
        event_id=EVSE_ID,
        event_notification_type=EventNotificationType.custom_monitor,
    )]
    notify_response = await cp.send_notify_event(data=event_data)
    assert notify_response is not None

    # Step 5-6: TransactionEvent Updated / CablePluggedIn / EVConnected
    plugged_event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.cable_plugged_in,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.ev_connected,
        },
    )
    response = await cp.send_transaction_event_request(plugged_event)
    assert response is not None

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
    response = await cp.send_transaction_event_request(charging_event)
    assert response is not None

    start_task.cancel()
