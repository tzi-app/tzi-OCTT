"""
TC_N_24 - Set Variable Monitoring - Periodic event
Use case: N08 | Requirements: N08.FR.02
N08.FR.02: When the CSMS receives a NotifyEventRequest The CSMS SHALL respond with an empty NotifyEventResponse.
    Precondition: When the CSMS receives an NotifyEventRequest
System under test: CSMS

Description:
    Charging Station sends a periodic NotifyEventRequest.

Purpose:
    To test that CSMS returns a NotifyEventResponse.

Main:
    1. OCTT sends NotifyEventRequest message
    2. CSMS returns NotifyEventResponse message
    Note: Steps 1 and 2 will be repeated n times

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
from utils import get_basic_auth_headers, now_iso

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_n_24():
    """Set Variable Monitoring - Periodic event."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Steps 1-2: Send NotifyEventRequest with periodic trigger, repeated 3 times
    for i in range(3):
        event_data = [{
            'event_id': i + 1,
            'timestamp': now_iso(),
            'trigger': EventTriggerEnumType.periodic,
            'actual_value': str(i * 10),
            'event_notification_type': EventNotificationEnumType.hard_wired_monitor,
            'component': {'name': 'EVSE', 'evse': {'id': EVSE_ID}},
            'variable': {'name': 'AvailabilityState'},
        }]
        response = await cp.send_notify_event(event_data)
        assert response is not None
        logging.info(f"TC_N_24 iteration {i + 1}: NotifyEventResponse received")

    logging.info("TC_N_24 completed successfully")
    start_task.cancel()
    await ws.close()
