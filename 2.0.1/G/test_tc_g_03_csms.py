"""
TC_G_03 - Change Availability EVSE - Operative to inoperative
Use case: G03 | Requirements: N/a
System under test: CSMS

Description:
    This test case covers how the CSMS requests the Charging Station to change the availability of one
    of the EVSEs from Operative to Inoperative. An EVSE is considered Operative in any status other than
    Faulted and Unavailable.

Purpose:
    To verify if the CSMS is able to perform the change availability mechanism as described at the OCPP
    specification.

Main:
    1. Execute Reusable State Unavailable for <Configured evseId>

Tool validations:
    N/a

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
    OperationalStatusEnumType,
)
from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType
from ocpp.v201.enums import EventTriggerEnumType, EventNotificationEnumType

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context
from trigger import send_call

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_g_03():
    """Change Availability EVSE - Operative to inoperative."""
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

    # Step 1: Execute Reusable State Unavailable for configured evseId
    # Trigger CSMS to send ChangeAvailabilityRequest
    async def trigger_change_availability():
        await asyncio.sleep(1)
        await send_call(BASIC_AUTH_CP, "ChangeAvailability", {
            "operationalStatus": "Inoperative",
            "evse": {"id": EVSE_ID},
        })

    trigger_task = asyncio.create_task(trigger_change_availability())

    await asyncio.wait_for(
        cp._received_change_availability.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    # Validate ChangeAvailabilityRequest content
    assert cp._change_availability_data is not None
    req_data = cp._change_availability_data
    assert req_data['operational_status'] == OperationalStatusEnumType.inoperative or \
           req_data['operational_status'] == 'Inoperative', \
        f"Expected operationalStatus=Inoperative, got {req_data['operational_status']}"

    # Validate evse.id per Unavailable reusable state tool validations
    evse = req_data.get('evse')
    assert evse is not None, "Expected evse to be present for EVSE-level change"
    if isinstance(evse, dict):
        assert evse.get('id') == EVSE_ID, \
            f"Expected evse.id={EVSE_ID}, got {evse.get('id')}"
        assert evse.get('connector_id') is None and evse.get('connectorId') is None, \
            f"Expected evse.connectorId to be omitted, got {evse}"

    # CS responds with Accepted (handled by on_change_availability handler)

    # CS notifies CSMS about the current state - StatusNotificationRequest
    await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusEnumType.unavailable,
        evse_id=EVSE_ID,
    )

    # CS sends NotifyEventRequest
    event_data = [
        EventDataType(
            trigger=EventTriggerEnumType.delta,
            actual_value='Unavailable',
            component=ComponentType(name='Connector', evse={"id": EVSE_ID}),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=EVSE_ID,
            event_notification_type=EventNotificationEnumType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)

    logging.info("TC_G_03 completed successfully")
    start_task.cancel()
    await ws.close()
