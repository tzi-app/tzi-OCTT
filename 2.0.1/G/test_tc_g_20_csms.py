"""
TC_G_20 - Connector status Notification - Lock Failure
Use case: G05 | Requirements: G05.FR.03
G05.FR.03: The CSMS SHALL respond with a NotifyEventResponse.
    Precondition: G05.FR.02
System under test: CSMS

Description:
    This test case describes how the EV Driver is prevented from starting a charge session at the
    Charging Station while the Connector is not locked properly.

Purpose:
    To verify if the CSMS responds on a notifyeventrequest as described at the OCPP specification.

Main:
    1. CS sends NotifyEventRequest with:
       - eventData.trigger = Delta
       - eventData.component.name = "ConnectorPlugRetentionLock"
       - eventData.variable.name = "Problem"
       - eventData.actualValue = "true"
    2. The CSMS responds with a NotifyEventResponse

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    EventTriggerEnumType,
    EventNotificationEnumType,
)
from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
async def test_tc_g_20():
    """Connector status Notification - Lock Failure."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available, evse_id=EVSE_ID)

    # Step 1-2: CS sends NotifyEventRequest with lock failure
    event_data = [
        EventDataType(
            trigger=EventTriggerEnumType.delta,
            actual_value='true',
            component=ComponentType(name='ConnectorPlugRetentionLock'),
            variable=VariableType(name='Problem'),
            timestamp=now_iso(),
            event_id=1,
            event_notification_type=EventNotificationEnumType.custom_monitor,
        )
    ]
    response = await cp.send_notify_event(data=event_data)
    assert response is not None

    logging.info("TC_G_20 completed successfully")
    start_task.cancel()
    await ws.close()
