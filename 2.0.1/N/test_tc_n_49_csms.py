"""
TC_N_49 - Alert Event - LowerThreshold/UpperThreshold cleared after reboot
Use case: N07 | Requirements: N/a
System under test: CSMS

Description:
    Charging Station sends NotifyEventRequest with eventData.cleared = true.

Purpose:
    To test that CSMS returns a NotifyEventResponse when it receives
    a NotifyEventRequest with eventData.cleared set to true.

Main:
    1. OCTT sends NotifyEventRequest with eventData.cleared = true
    2. CSMS responds NotifyEventResponse

Tool validations:
    * N/a

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
async def test_tc_n_49():
    """Alert Event - LowerThreshold/UpperThreshold cleared after reboot."""
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

    # Steps 1-2: Send NotifyEventRequest with cleared = true
    event_data = [{
        'event_id': 1,
        'timestamp': now_iso(),
        'trigger': EventTriggerEnumType.alerting,
        'actual_value': '0',
        'cleared': True,
        'event_notification_type': EventNotificationEnumType.hard_wired_monitor,
        'component': {'name': 'EVSE', 'evse': {'id': EVSE_ID}},
        'variable': {'name': 'AvailabilityState'},
    }]
    response = await cp.send_notify_event(event_data)
    assert response is not None

    logging.info("TC_N_49 completed successfully")
    start_task.cancel()
    await ws.close()
