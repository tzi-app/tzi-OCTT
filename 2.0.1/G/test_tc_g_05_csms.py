"""
TC_G_05 - Change Availability Charging Station - Operative to inoperative
Use case: G04 | Requirements: N/a
System under test: CSMS

Description:
    This test case describes how the CSMS requests the Charging Station to change the availability from
    operative to inoperative. A Charging Station is considered Operative when it is charging or ready
    for charging. A Charging Station is considered Inoperative when it does not allow any charging.

Purpose:
    To verify if the CSMS is able to perform the change availability mechanism as described at the OCPP
    specification.

Main:
    Manual Action: Request the CSMS to change the availability of the Charging Station to Inoperative.
    1. The CSMS sends a ChangeAvailabilityRequest
    2. CS responds with ChangeAvailabilityResponse (status=Accepted)
    3. CS notifies CSMS about current state (StatusNotificationRequest + NotifyEventRequest)
    4. The CSMS responds accordingly.

Tool validations:
    * Step 1: ChangeAvailabilityRequest
      - operationalStatus = Inoperative
      - evseId = omit
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
from utils import get_basic_auth_headers, now_iso

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_g_05():
    """Change Availability Charging Station - Operative to inoperative."""
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

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available, evse_id=EVSE_ID)

    # Step 1-2: Wait for CSMS to send ChangeAvailabilityRequest
    # Manual action: Request the CSMS to change the CS availability to Inoperative
    await asyncio.wait_for(
        cp._received_change_availability.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate ChangeAvailabilityRequest content
    assert cp._change_availability_data is not None
    req_data = cp._change_availability_data
    assert req_data['operational_status'] == OperationalStatusEnumType.inoperative or \
           req_data['operational_status'] == 'Inoperative', \
        f"Expected operationalStatus=Inoperative, got {req_data['operational_status']}"

    # evseId and connectorId should be omitted (whole station)
    evse = req_data.get('evse')
    assert evse is None, f"Expected evse to be omitted for station-level, got {evse}"

    # Step 3: CS notifies CSMS about the current state of all connectors
    await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusEnumType.unavailable,
        evse_id=EVSE_ID,
    )

    # NotifyEventRequest
    event_data = [
        EventDataType(
            trigger=EventTriggerEnumType.delta,
            actual_value='Unavailable',
            component=ComponentType(name='Connector'),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=EVSE_ID,
            event_notification_type=EventNotificationEnumType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)

    logging.info("TC_G_05 completed successfully")
    start_task.cancel()
    await ws.close()
