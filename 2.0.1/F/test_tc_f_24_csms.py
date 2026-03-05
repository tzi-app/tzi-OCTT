"""
TC_F_24 - Trigger message - StatusNotification - Specific EVSE - Occupied
Use case: F06 | Requirements: F06.FR.01, F06.FR.02, F06.FR.13
F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to receive.
F06.FR.02: The requested message SHALL be leading. If the specified evseId is not relevant to the message, it SHALL be ignored. In such cases the requested message SHALL still be sent.
    Precondition: F06.FR.01. For every such requested message.
F06.FR.13: When sending a TriggerMessageRequest with requestedMessage set to StatusNotification, the CSMS SHALL include the evse field. StatusNotification messages can only be sent at connector level.
    Precondition: When sending a TriggerMessageRequest with requestedMessage set to: StatusNotification
System under test: CSMS

Description:
    The CSMS can request a Charging Station to send Charging Station-initiated messages. In the request
    the CSMS indicates which message it wishes to receive.

Purpose:
    To verify if the CSMS is able to trigger the Charging Station to send a StatusNotificationRequest
    for a specific occupied EVSE, using a TriggerMessageRequest.

Main:
    1. CS sends StatusNotificationRequest (connectorStatus=Occupied) + NotifyEventRequest (Occupied)
    2. CSMS responds accordingly
    3. CSMS sends TriggerMessageRequest (requestedMessage=StatusNotification, evse.id=<configured>)
    4. CS responds with TriggerMessageResponse (status=Accepted)
    5. CS sends StatusNotificationRequest (connectorStatus=Occupied) + NotifyEventRequest (Occupied)
    6. CSMS responds accordingly

Tool validations:
    * Step 1 (Step 3 in spec): TriggerMessageRequest
      - requestedMessage must be StatusNotification
      - evse.id must be <Configured evseId>

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
    MessageTriggerEnumType,
)
from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType, EVSEType
from ocpp.v201.enums import (
    EventTriggerEnumType as EventTriggerType,
    EventNotificationEnumType as EventNotificationType,
)

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


async def _send_occupied_status(cp, evse_id, connector_id):
    """Send StatusNotification(Occupied) + NotifyEvent(Occupied) for the given EVSE/connector."""
    await cp.send_status_notification(
        connector_id=connector_id,
        status=ConnectorStatusEnumType.occupied,
        evse_id=evse_id,
    )
    event_data = [
        EventDataType(
            trigger=EventTriggerType.delta,
            actual_value='Occupied',
            component=ComponentType(
                name='Connector',
                evse=EVSEType(id=evse_id, connector_id=connector_id),
            ),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=1,
            event_notification_type=EventNotificationType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)


@pytest.mark.asyncio
async def test_tc_f_24():
    """Trigger message - StatusNotification - Specific EVSE - Occupied."""
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

    await cp.send_status_notification(1, ConnectorStatusEnumType.available, evse_id=EVSE_ID)

    # Step 1-2: CS notifies CSMS about Occupied state
    await _send_occupied_status(cp, EVSE_ID, CONNECTOR_ID)

    # Step 3-4: Trigger CSMS to send TriggerMessageRequest
    async def trigger_msg():
        await asyncio.sleep(1)
        await send_call(BASIC_AUTH_CP, "TriggerMessage", {
            "requestedMessage": "StatusNotification",
            "evse": {"id": EVSE_ID},
        })

    trigger_task = asyncio.create_task(trigger_msg())

    await asyncio.wait_for(
        cp._received_trigger_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    # Validate Step 3: TriggerMessageRequest content
    assert cp._trigger_message_data == MessageTriggerEnumType.status_notification or \
           cp._trigger_message_data == 'StatusNotification', \
        f"Expected requestedMessage=StatusNotification, got {cp._trigger_message_data}"

    assert cp._trigger_message_evse is not None, "Expected evse to be present"
    evse = cp._trigger_message_evse
    if isinstance(evse, dict):
        assert evse.get('id') == EVSE_ID, \
            f"Expected evse.id={EVSE_ID}, got {evse.get('id')}"

    # Step 5-6: CS sends StatusNotification(Occupied) + NotifyEvent(Occupied) again
    await _send_occupied_status(cp, EVSE_ID, CONNECTOR_ID)

    logging.info("TC_F_24 completed successfully")
    start_task.cancel()
    await ws.close()
