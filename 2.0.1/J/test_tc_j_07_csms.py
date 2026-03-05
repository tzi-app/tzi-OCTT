"""
TC_J_07 - Sampled Meter Values - EventType Started - EVSE known
Use case: J02 | Requirement: J02.FR.19
J02.FR.19: When CSMS receives a TransactionEventRequest CSMS SHALL respond with TransactionEventResponse. Failing to respond with TransactionEventRespon se might cause the Charging Station to try the same message
    Precondition: When CSMS receives a TransactionEventRequest
System under test: CSMS

Description:
    The Charging Station samples the electrical meter or other sensor/transducer hardware to provide
    information about its Meter Values. Depending on configuration settings, the Charging Station will
    send Meter Values.

Purpose:
    To verify if the CSMS is able to handle a Charging Station sending start sampled Meter Values,
    when a transaction starts.

Before:
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): N/a

Main:
    1. Execute Reusable State EVConnectedPreSession
       - The TransactionEventRequest contains the MeterValue field.
       - sampledValue.context is Transaction.Begin

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.call import TransactionEvent
from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType
from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    EventTriggerEnumType as EventTriggerType,
    EventNotificationEnumType as EventNotificationType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_j_07(connection):
    """Sampled Meter Values - EventType Started - EVSE known (J02.FR.19).
    J02.FR.19: When CSMS receives a TransactionEventRequest CSMS SHALL respond with TransactionEventResponse. Failing to respond with TransactionEventRespon se might cause the Charging Station to try the same message
        Precondition: When CSMS receives a TransactionEventRequest
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Boot
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1: Execute Reusable State EVConnectedPreSession (inline with MeterValue)
    # StatusNotification - Occupied
    await cp.send_status_notification(connector_id=CONNECTOR_ID, status=ConnectorStatusEnumType.occupied)

    # NotifyEvent - Occupied
    event_data = [
        EventDataType(
            trigger=EventTriggerType.delta,
            actual_value='Occupied',
            component=ComponentType(name='Connector'),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=EVSE_ID,
            event_notification_type=EventNotificationType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)

    # TransactionEvent Started with MeterValue containing Transaction.Begin
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
        meter_value=[{
            'timestamp': now_iso(),
            'sampled_value': [{
                'value': 0.0,
                'context': 'Transaction.Begin',
            }],
        }],
    )
    started_response = await cp.send_transaction_event_request(started_event)
    assert started_response is not None

    start_task.cancel()
