"""
TC_H_15 - Reserve a connector with a specific type - Success
Use case: H01(S3), H03 | Requirements: N/a
System under test: CSMS

Description:
    The CSMS is able to reserve an EVSE with a connector with a specific type for a specific IdToken by
    sending a ReserveNowRequest with a connectorType.

Purpose:
    To verify if the CSMS is able to request the Charging Station to reserve an EVSE with a connector
    with a specific type, until the EV Driver with the specified IdToken arrives.

Main:
    Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific ConnectorType.
    1. The CSMS sends a ReserveNowRequest
    2. CS responds with ReserveNowResponse (status=Accepted)
    3. CS notifies CSMS (StatusNotificationRequest connectorStatus=Reserved + NotifyEventRequest)
    4. The CSMS responds accordingly.

Tool validations:
    * Step 1: ReserveNowRequest
      - evseId must be omitted
      - connectorType must be <Configured connectorType>
      - idToken.idToken <Configured valid_idtoken_idtoken>
      - idToken.type <Configured valid_idtoken_type>

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
    VALID_ID_TOKEN            - Valid idToken value
    VALID_ID_TOKEN_TYPE       - Valid idToken type
    CONFIGURED_CONNECTOR_TYPE - Connector type (default cType2)
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
from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType, EVSEType

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
CONFIGURED_CONNECTOR_TYPE = os.environ['CONFIGURED_CONNECTOR_TYPE']


@pytest.mark.asyncio
async def test_tc_h_15():
    """Reserve a connector with a specific type - Success."""
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

    # Step 1-2: Wait for CSMS to send ReserveNowRequest
    await asyncio.wait_for(
        cp._received_reserve_now.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate ReserveNowRequest content
    assert cp._reserve_now_data is not None
    req_data = cp._reserve_now_data

    # evseId must be omitted
    assert req_data.get('evse_id') is None, \
        f"Expected evseId to be omitted, got {req_data.get('evse_id')}"

    # connectorType must be the configured type
    assert req_data.get('connector_type') is not None, \
        "Expected connectorType to be provided"
    assert str(req_data['connector_type']) == CONFIGURED_CONNECTOR_TYPE or \
           req_data['connector_type'] == CONFIGURED_CONNECTOR_TYPE, \
        f"Expected connectorType={CONFIGURED_CONNECTOR_TYPE}, got {req_data['connector_type']}"

    id_token = req_data['id_token']
    if isinstance(id_token, dict):
        assert id_token.get('id_token') == VALID_ID_TOKEN, \
            f"Expected idToken={VALID_ID_TOKEN}, got {id_token.get('id_token')}"
        assert id_token.get('type') == VALID_ID_TOKEN_TYPE, \
            f"Expected idToken.type={VALID_ID_TOKEN_TYPE}, got {id_token.get('type')}"

    # Step 3-4: CS notifies CSMS about the status change - Reserved
    await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusEnumType.reserved,
        evse_id=EVSE_ID,
    )

    event_data = [
        EventDataType(
            trigger=EventTriggerEnumType.delta,
            actual_value='Reserved',
            component=ComponentType(name='Connector', evse=EVSEType(id=EVSE_ID, connector_id=CONNECTOR_ID)),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=EVSE_ID,
            event_notification_type=EventNotificationEnumType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)

    logging.info("TC_H_15 completed successfully")
    start_task.cancel()
    await ws.close()
