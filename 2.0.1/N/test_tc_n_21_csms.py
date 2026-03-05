"""
TC_N_21 - Alert Event - HardWiredMonitor
Use case: N07 | Requirements: N07.FR.03
N07.FR.03: When the CSMS receives an NotifyEventRequest The CSMS SHALL respond with an empty NotifyEventResponse.
    Precondition: When the CSMS receives an NotifyEventRequest
System under test: CSMS

Description:
    Charging Station sends NotifyEventRequest for HardWiredMonitor,
    CSMS responds with NotifyEventResponse.

Purpose:
    To test that CSMS returns a NotifyEventResponse when it receives
    a NotifyEventRequest with eventNotificationType = HardWiredMonitor.

Main:
    1. OCTT sends NotifyEventRequest with eventNotificationType = HardWiredMonitor
    2. CSMS responds NotifyEventResponse (empty body)

Tool validations:
    * Step 2: NotifyEventResponse with empty body

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
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

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_n_21():
    """Alert Event - HardWiredMonitor."""
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

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Steps 1-2: Send NotifyEventRequest with HardWiredMonitor
    event_data = [{
        'event_id': 1,
        'timestamp': now_iso(),
        'trigger': EventTriggerEnumType.alerting,
        'actual_value': '1',
        'event_notification_type': EventNotificationEnumType.hard_wired_monitor,
        'component': {'name': 'EVSE', 'evse': {'id': EVSE_ID}},
        'variable': {'name': 'AvailabilityState'},
    }]
    response = await cp.send_notify_event(event_data)
    assert response is not None

    logging.info("TC_N_21 completed successfully")
    start_task.cancel()
    await ws.close()
