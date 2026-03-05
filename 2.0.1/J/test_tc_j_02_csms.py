"""
TC_J_02 - Clock-aligned Meter Values - Transaction ongoing
Use case: J01 | Requirement: J01.FR.18
J01.FR.18: When CSMS receives a MeterValuesRequest CSMS SHALL respond with MeterValuesResponse. Failing to respond with MeterValuesResponse might cause the Charging Station to try the same message again.
    Precondition: When CSMS receives a MeterValuesRequest
System under test: CSMS

Description:
    The Charging Station samples the electrical meter or other sensor/transducer hardware to provide
    information about its Meter Values. Depending on configuration settings, the Charging Station will
    send Meter Values.

Purpose:
    To verify if the CSMS is able to handle a Charging Station sending clock-aligned Meter Values,
    when there is an ongoing transaction.

Before:
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): State is EnergyTransferStarted for <Configured evseId>

Main:
    1. The OCTT notifies the CSMS about its measured Meter Values.
       Message: MeterValuesRequest
         - sampledValue.context is Sample.Clock
       Message: NotifyEventRequest
         - trigger is Periodic
         - component.name is FiscalMetering
       Note: Executed for evseId=0 and all configured idle EVSE.

    3. The OCTT sends a TransactionEventRequest
       With triggerReason is MeterValueClock, eventType is Updated
         - sampledValue.context is Sample.Clock
       Note: Executed every clock-aligned interval until transaction duration reached.

    4. The CSMS responds with a TransactionEventResponse

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
import math
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

CLOCK_ALIGNED_INTERVAL = int(os.environ['CLOCK_ALIGNED_METER_VALUES_INTERVAL'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_j_02(connection):
    """Clock-aligned Meter Values - Transaction ongoing (J01.FR.18).
    J01.FR.18: When CSMS receives a MeterValuesRequest CSMS SHALL respond with MeterValuesResponse. Failing to respond with MeterValuesResponse might cause the Charging Station to try the same message again.
        Precondition: When CSMS receives a MeterValuesRequest
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

    iterations = max(1, math.ceil(TRANSACTION_DURATION / CLOCK_ALIGNED_INTERVAL))
    base_timestamp = datetime.now(timezone.utc)

    # Step 1-4: Clock-aligned periodic messages during ongoing transaction.
    for i in range(iterations):
        tick_timestamp = (base_timestamp + timedelta(seconds=i * CLOCK_ALIGNED_INTERVAL)).isoformat()

        # Step 1-2: MeterValues for evseId=0 and idle EVSEs (clock-aligned, Sample.Clock)
        evse_id = 0
        meter_response = await cp.send_meter_values(
            evse_id=evse_id,
            sampled_values=[{
                'value': float((i + 1) * 100),
                'context': 'Sample.Clock',
            }],
            timestamp=tick_timestamp,
        )
        assert meter_response is not None

        # NotifyEventRequest for FiscalMetering
        event_data = [
            EventDataType(
                trigger=EventTriggerType.periodic,
                actual_value=str((i + 1) * 100),
                component=ComponentType(name='FiscalMetering'),
                variable=VariableType(name='MeterValue'),
                timestamp=tick_timestamp,
                event_id=i + 1,
                event_notification_type=EventNotificationType.custom_monitor,
            )
        ]
        notify_response = await cp.send_notify_event(data=event_data)
        assert notify_response is not None

        # Step 3-4: TransactionEventRequest with triggerReason=MeterValueClock for the active EVSE
        meter_clock_event = TransactionEvent(
            event_type=TransactionEventType.updated,
            timestamp=tick_timestamp,
            trigger_reason=TriggerReasonType.meter_value_clock,
            seq_no=cp.next_seq_no(),
            transaction_info={
                'transaction_id': transaction_id,
                'charging_state': ChargingStateType.charging,
            },
            evse={
                'id': EVSE_ID,
                'connector_id': CONNECTOR_ID,
            },
            meter_value=[{
                'timestamp': tick_timestamp,
                'sampled_value': [{
                    'value': float((i + 1) * 100),
                    'context': 'Sample.Clock',
                }],
            }],
        )
        tx_response = await cp.send_transaction_event_request(meter_clock_event)
        assert tx_response is not None

        if i < iterations - 1:
            await asyncio.sleep(CLOCK_ALIGNED_INTERVAL)

    start_task.cancel()
