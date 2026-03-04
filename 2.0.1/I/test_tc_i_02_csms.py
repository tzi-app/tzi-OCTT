"""
TC_I_02 - Show EV Driver Final Total Cost After Charging
Use case: I03 | Requirements: I03.FR.02
I03.FR.02: Charging Station was online when transaction stopped The Charging Station SHALL display the total cost to the EV Driver.
    Precondition: I03.FR.01 AND When Total Cost is known to the CSMS.
System under test: CSMS

Description:
    After a charging session ends, the CSMS includes the final total cost in the
    TransactionEventResponse for the Ended transaction event.

Purpose:
    To verify if the CSMS includes the totalCost field in the TransactionEventResponse
    when the Charging Station sends a TransactionEventRequest with eventType=Ended.

Before:
    Memory State: CSMS is configured with a tariff based on energy consumed.

Main:
    1. Execute Reusable State EVConnectedPreSession
       - TransactionEventRequest contains meterValue sampledValue[0].value=1000,
         sampledValue[0].context=Transaction.Begin
    2. Execute Reusable State Authorized
    3. Execute Reusable State EnergyTransferStarted
    4. Execute Reusable State StopAuthorized
    5. Execute Reusable State EVConnectedPostSession
    6. CS sends StatusNotificationRequest (connectorStatus=Available) and NotifyEventRequest
       (trigger=Delta, actualValue=Available, component.name=Connector, variable.name=AvailabilityState)
    7. CS sends TransactionEventRequest (eventType=Ended, triggerReason=EVCommunicationLost,
       chargingState=Idle, stoppedReason=EVDisconnected, meterValue=6000, context=Transaction.End)
    8. CSMS responds TransactionEventResponse

Tool validations:
    * Final TransactionEventResponse - totalCost must NOT be omitted

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    VALID_ID_TOKEN            - Valid idToken value
    VALID_ID_TOKEN_TYPE       - Valid idToken type
"""
import asyncio
import logging
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.call import TransactionEvent
from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType
from ocpp.v201.enums import (
    ConnectorStatusEnumType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
    ReasonEnumType as StoppedReasonType,
    EventTriggerEnumType as EventTriggerType,
    EventNotificationEnumType as EventNotificationType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso
from reusable_states.stop_authorized import stop_authorized
from reusable_states.ev_connected_post_session import ev_connected_post_session
from reusable_states.authorized import authorized

logging.basicConfig(level=logging.INFO)

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
async def test_tc_i_02(connection):
    """Show EV Driver Final Total Cost After Charging."""
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Step 1: Execute Reusable State EVConnectedPreSession with required meter begin value
    await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusEnumType.occupied,
    )

    occupied_event_data = [
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
    await cp.send_notify_event(data=occupied_event_data)

    ev_connected_event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.cable_plugged_in,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.ev_connected,
        },
        meter_value=[{
            'timestamp': now_iso(),
            'sampled_value': [{
                'value': 1000,
                'context': 'Transaction.Begin',
            }],
        }],
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    ev_connected_response = await cp.send_transaction_event_request(ev_connected_event)
    assert ev_connected_response is not None

    # Step 2: Execute Reusable State Authorized
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                     ev_connected_pre_session=True)

    # Step 3: Execute Reusable State EnergyTransferStarted (Part 2 only, already EVConnected)
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

    # Step 4-5: Execute Reusable States StopAuthorized and EVConnectedPostSession
    await stop_authorized(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                          transaction_id=transaction_id)
    await ev_connected_post_session(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                    transaction_id=transaction_id)

    # Step 6: StatusNotification - Available
    await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusEnumType.available,
    )

    # Step 6 (cont): NotifyEvent - Available
    event_data = [
        EventDataType(
            trigger=EventTriggerType.delta,
            actual_value='Available',
            component=ComponentType(name='Connector'),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=EVSE_ID,
            event_notification_type=EventNotificationType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)

    # Step 8-9: TransactionEvent Ended - EVCommunicationLost / Idle / EVDisconnected
    ended_event = TransactionEvent(
        event_type=TransactionEventType.ended,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.ev_communication_lost,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.idle,
            'stopped_reason': StoppedReasonType.ev_disconnected,
        },
        meter_value=[{
            'timestamp': now_iso(),
            'sampled_value': [{
                'value': 6000,
                'context': 'Transaction.End',
            }],
        }],
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    ended_response = await cp.send_transaction_event_request(ended_event)
    assert ended_response is not None

    # Tool validation: totalCost must NOT be omitted
    assert ended_response.total_cost is not None, \
        "TransactionEventResponse for Ended event must include totalCost (was omitted/None)"
    logging.info(f"TransactionEventResponse totalCost={ended_response.total_cost}")

    logging.info("TC_I_02 completed successfully")
    start_task.cancel()
