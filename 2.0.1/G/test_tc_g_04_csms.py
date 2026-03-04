"""
TC_G_04 - Change Availability EVSE - Inoperative to operative
Use case: G03 | Requirements: N/a
System under test: CSMS

Description:
    This test case covers how the CSMS requests the Charging Station to change the availability of one
    of the EVSEs from Inoperative to Operative. An EVSE is considered Operative in any status other than
    Faulted and Unavailable.

Purpose:
    To verify if the CSMS is able to perform the change availability mechanism as described at the OCPP
    specification.

Before:
    Memory State: Unavailable for <Configured evseId>

Main:
    Manual Action: Request the CSMS to change the availability of an EVSE to Operative.
    1. The CSMS sends a ChangeAvailabilityRequest
    2. CS responds with ChangeAvailabilityResponse (status=Accepted)
    3. CS notifies CSMS about current state (StatusNotificationRequest + NotifyEventRequest)
    4. The CSMS responds accordingly.

Tool validations:
    * Step 1: ChangeAvailabilityRequest
      - operationalStatus = Operative
      - evse.id = <Configured evseId>
      - connectorId = omit

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
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_g_04():
    """Change Availability EVSE - Inoperative to operative."""
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

    # Before: Memory State is Unavailable - report connector as Unavailable
    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.unavailable, evse_id=EVSE_ID)

    # Step 1-2: Wait for CSMS to send ChangeAvailabilityRequest (Operative)
    # Manual action: Request the CSMS to change the availability of an EVSE to Operative
    await asyncio.wait_for(
        cp._received_change_availability.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate ChangeAvailabilityRequest content
    assert cp._change_availability_data is not None
    req_data = cp._change_availability_data
    assert req_data['operational_status'] == OperationalStatusEnumType.operative or \
           req_data['operational_status'] == 'Operative', \
        f"Expected operationalStatus=Operative, got {req_data['operational_status']}"

    evse = req_data.get('evse')
    assert evse is not None, "Expected evse to be present for EVSE-level change"
    if isinstance(evse, dict):
        assert evse.get('id') == EVSE_ID, \
            f"Expected evse.id={EVSE_ID}, got {evse.get('id')}"
        assert evse.get('connector_id') is None and evse.get('connectorId') is None, \
            f"Expected evse.connectorId to be omitted, got {evse}"

    # Step 3: CS notifies CSMS about the current state - Available
    await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusEnumType.available,
        evse_id=EVSE_ID,
    )

    # NotifyEventRequest
    event_data = [
        EventDataType(
            trigger=EventTriggerEnumType.delta,
            actual_value='Available',
            component=ComponentType(name='Connector', evse={"id": EVSE_ID}),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=EVSE_ID,
            event_notification_type=EventNotificationEnumType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)

    logging.info("TC_G_04 completed successfully")
    start_task.cancel()
    await ws.close()
