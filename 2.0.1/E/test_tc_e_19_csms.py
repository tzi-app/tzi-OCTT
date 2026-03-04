"""
TC_E_19 - Stop transaction options - ParkingBayUnoccupied
Use case: E06(S1) | Requirement: E06.FR.01
E06.FR.01: TxStopPoint contains: ParkingBayOccupancy AND Parking Bay Detector no longer detects the "EV" The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS.
    Precondition: TxStopPoint contains: ParkingBayOccupancy AND Parking Bay Detector no longer detects the "EV"
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that stops a transaction when the EV left
the parking bay (TxStopPoint = ParkingBayOccupancy).

Before: Reusable State EVDisconnected

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
    ReasonEnumType as StoppedReasonType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.stop_authorized import stop_authorized
from reusable_states.ev_connected_post_session import ev_connected_post_session

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
async def test_tc_e_19(connection):
    """Stop transaction options - ParkingBayUnoccupied (E06.FR.01).
    E06.FR.01: TxStopPoint contains: ParkingBayOccupancy AND Parking Bay Detector no longer detects the "EV" The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS.
        Precondition: TxStopPoint contains: ParkingBayOccupancy AND Parking Bay Detector no longer detects the "EV"
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Before: EVDisconnected
    # Build up through Authorized → EnergyTransferStarted → StopAuthorized → EVConnectedPostSession
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)
    await stop_authorized(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                           transaction_id=transaction_id)
    await ev_connected_post_session(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                    transaction_id=transaction_id)

    # EVDisconnected state (without ending the transaction, since TxStopPoint=ParkingBayOccupancy)
    # The transaction ends on EVDeparted (parking bay), not on EVDisconnected.
    status_response = await cp.send_status_notification(
        connector_id=CONNECTOR_ID, status=ConnectorStatusType.available
    )
    assert status_response is not None

    event_data = [EventDataType(
        trigger=EventTriggerType.delta,
        actual_value='Available',
        component=ComponentType(name='Connector'),
        variable=VariableType(name='AvailabilityState'),
        timestamp=now_iso(),
        event_id=EVSE_ID,
        event_notification_type=EventNotificationType.custom_monitor,
    )]
    notify_response = await cp.send_notify_event(data=event_data)
    assert notify_response is not None

    ev_comm_lost_event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.ev_communication_lost,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.idle,
        },
    )
    ev_comm_lost_response = await cp.send_transaction_event_request(ev_comm_lost_event)
    assert ev_comm_lost_response is not None

    # Step 1-2: TransactionEvent Ended / EVDeparted / Local
    end_event = TransactionEvent(
        event_type=TransactionEventType.ended,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.ev_departed,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'stopped_reason': StoppedReasonType.local,
        },
    )
    end_response = await cp.send_transaction_event_request(end_event)
    assert end_response is not None

    start_task.cancel()
