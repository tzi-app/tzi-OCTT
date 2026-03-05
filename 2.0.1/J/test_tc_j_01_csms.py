"""
TC_J_01 - Clock-aligned Meter Values - No transaction ongoing
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
    when there is no ongoing transaction.

Before:
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): N/a

Main:
    1. The OCTT notifies the CSMS about its measured Meter Values.
       Message: MeterValuesRequest
         - timestamp at clock-aligned intervals
         - sampledValue.context is Sample.Clock
       Message: NotifyEventRequest
         - trigger is Periodic
         - component.name is FiscalMetering

    2. The CSMS responds accordingly.

    Note(s):
      - Executed for evseId=0 and all configured EVSE.
      - Ends after 3 Meter Value messages.

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
from datetime import datetime, timedelta, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType
from ocpp.v201.enums import (
    EventTriggerEnumType as EventTriggerType,
    EventNotificationEnumType as EventNotificationType,
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])

METER_VALUE_COUNT = 3
CLOCK_ALIGNED_INTERVAL = int(os.environ['CLOCK_ALIGNED_METER_VALUES_INTERVAL'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_j_01(connection):
    """Clock-aligned Meter Values - No transaction ongoing (J01.FR.18).
    J01.FR.18: When CSMS receives a MeterValuesRequest CSMS SHALL respond with MeterValuesResponse. Failing to respond with MeterValuesResponse might cause the Charging Station to try the same message again.
        Precondition: When CSMS receives a MeterValuesRequest
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Boot
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Execute for evseId=0 and configured EVSE, 3 meter value messages each
    evse_ids = [0] if EVSE_ID == 0 else [0, EVSE_ID]

    event_counter = 0
    for evse_id in evse_ids:
        base_timestamp = datetime.now(timezone.utc)
        for i in range(METER_VALUE_COUNT):
            tick_timestamp = (base_timestamp + timedelta(seconds=i * CLOCK_ALIGNED_INTERVAL)).isoformat()

            # Step 1: MeterValuesRequest with context=Sample.Clock
            meter_response = await cp.send_meter_values(
                evse_id=evse_id,
                sampled_values=[{
                    'value': float(i * 100),
                    'context': 'Sample.Clock',
                }],
                timestamp=tick_timestamp,
            )
            assert meter_response is not None

            # Step 1 (cont): NotifyEventRequest with trigger=Periodic, component.name=FiscalMetering
            event_counter += 1
            event_data = [
                EventDataType(
                    trigger=EventTriggerType.periodic,
                    actual_value=str(i * 100),
                    component=ComponentType(name='FiscalMetering'),
                    variable=VariableType(name='MeterValue'),
                    timestamp=tick_timestamp,
                    event_id=event_counter,
                    event_notification_type=EventNotificationType.custom_monitor,
                )
            ]
            notify_response = await cp.send_notify_event(data=event_data)
            assert notify_response is not None

            if i < METER_VALUE_COUNT - 1:
                await asyncio.sleep(CLOCK_ALIGNED_INTERVAL)

    start_task.cancel()
