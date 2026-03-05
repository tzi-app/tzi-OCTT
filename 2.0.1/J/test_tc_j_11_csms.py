"""
TC_J_11 - Sampled Meter Values - Signed
Use case: J02 | Requirement: J02.FR.21
J02.FR.21: SampledDataSignReadings is true The Charging Station SHALL retrieve signed meter values from components that support data signing and put them in the signedMeterValue field.
    Precondition: SampledDataSignReadings is true
System under test: CSMS

Description:
    The Charging Station samples the electrical meter or other sensor/transducer hardware to provide
    information about its Meter Values. Depending on configuration settings, the Charging Station will
    send Meter Values.

Purpose:
    To verify if the CSMS is able to handle a Charging Station sending sampled Meter Values, when a
    transaction ends, with signed meter values.

Before:
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): State is EnergyTransferStarted

Main:
    1. Execute Reusable State EVDisconnected
       - The TransactionEventRequest containing eventType Ended contains the MeterValue field.
       - sampledValue.context is Sample.Periodic AND the last one has Transaction.End
       - sampledValue.signedMeterValue is <Generated SignedMeterValueType>

    Note(s):
      - This step will be executed after the configured transaction duration is reached.
      - This causes the transaction to stop.

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    VALID_ID_TOKEN            - Valid idToken value
    VALID_ID_TOKEN_TYPE       - Valid idToken type
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    TRANSACTION_DURATION      - Duration of the transaction in seconds (default 5)
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

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
    ReasonEnumType as StoppedReasonType,
    ChargingStateEnumType as ChargingStateType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])
TX_ENDED_METER_VALUES_INTERVAL = int(os.environ['TX_ENDED_METER_VALUES_INTERVAL'])

# Sample signed meter value data for testing
SIGNED_METER_VALUE = {
    'signed_meter_data': 'SGVsbG8gV29ybGQ=',  # Base64 encoded sample data
    'signing_method': 'ECDSAP256SHA256',
    'encoding_method': 'DLMS Message',
    'public_key': 'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEExamplePublicKeyData==',
}


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_j_11(connection):
    """Sampled Meter Values - Signed (J02.FR.21).
    J02.FR.21: SampledDataSignReadings is true The Charging Station SHALL retrieve signed meter values from components that support data signing and put them in the signedMeterValue field.
        Precondition: SampledDataSignReadings is true
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Boot
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Before: EnergyTransferStarted
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Wait for configured transaction duration
    await asyncio.sleep(TRANSACTION_DURATION)

    # Step 1: Execute Reusable State EVDisconnected (inline with signed meter values)
    # StatusNotification - Available
    await cp.send_status_notification(connector_id=CONNECTOR_ID, status=ConnectorStatusEnumType.available, evse_id=EVSE_ID)

    # NotifyEvent - Available
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

    tx_end_base = datetime.now(timezone.utc)
    tx_end_second = (tx_end_base + timedelta(seconds=TX_ENDED_METER_VALUES_INTERVAL)).isoformat()

    # TransactionEvent Ended with sampled MeterValues and signed values
    end_event = TransactionEvent(
        event_type=TransactionEventType.ended,
        timestamp=tx_end_second,
        trigger_reason=TriggerReasonType.ev_communication_lost,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.idle,
            'stopped_reason': StoppedReasonType.ev_disconnected,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
        meter_value=[
            {
                'timestamp': tx_end_base.isoformat(),
                'sampled_value': [
                    {
                        'value': 500.0,
                        'context': 'Sample.Periodic',
                        'signed_meter_value': SIGNED_METER_VALUE,
                    },
                ],
            },
            {
                'timestamp': tx_end_second,
                'sampled_value': [
                    {
                        'value': 510.0,
                        'context': 'Sample.Periodic',
                        'signed_meter_value': SIGNED_METER_VALUE,
                    },
                    {
                        'value': 510.0,
                        'context': 'Transaction.End',
                        'signed_meter_value': SIGNED_METER_VALUE,
                    },
                ],
            },
        ],
    )
    end_response = await cp.send_transaction_event_request(end_event)
    assert end_response is not None

    start_task.cancel()
