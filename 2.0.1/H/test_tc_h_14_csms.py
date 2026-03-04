"""
TC_H_14 - Reserve an unspecified EVSE - Amount of EVSEs available equals the amount of reservations
Use case: H01(S1) | Requirements: N/a
System under test: CSMS

Description:
    The CSMS is able to reserve an unspecified EVSE for a specific IdToken by sending a ReserveNowRequest
    without an evseId.

Purpose:
    To verify if the CSMS is able to handle that the Charging Station sets all available EVSE to reserved,
    when the amount of EVSEs available equals the amount of reservations.

Main:
    Manual Action: Trigger the CSMS to send a ReserveNowRequest for an unspecified EVSE.
    1. The CSMS sends a ReserveNowRequest
    2. CS responds with ReserveNowResponse (status=Accepted)
    Note: This step needs to be executed for the amount of EVSE configured for the OCTT.
    3. CS notifies CSMS (StatusNotificationRequest connectorStatus=Reserved + NotifyEventRequest)
    4. The CSMS responds accordingly.
    Note: Step 3 will be executed after the last ReserveNowRequest has been sent from step 1.

Tool validations:
    * Step 1: ReserveNowRequest
      - evseId must be omitted
      - connectorType must be omitted
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
    CONFIGURED_NUMBER_OF_EVSES - Number of EVSEs configured in the test system (default 1)
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
from utils import get_basic_auth_headers, now_iso

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
CONFIGURED_NUMBER_OF_EVSES = int(os.environ['CONFIGURED_NUMBER_OF_EVSES'])


@pytest.mark.asyncio
async def test_tc_h_14():
    """Reserve an unspecified EVSE - Amount of EVSEs equals reservations."""
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

    # Send initial Available status for all EVSEs
    for evse_idx in range(CONFIGURED_NUMBER_OF_EVSES):
        await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available, evse_id=evse_idx + 1)

    # Step 1-2: Repeat for the configured amount of EVSEs.
    assert CONFIGURED_NUMBER_OF_EVSES >= 1, \
        f"Expected CONFIGURED_NUMBER_OF_EVSES >= 1, got {CONFIGURED_NUMBER_OF_EVSES}"

    for request_index in range(CONFIGURED_NUMBER_OF_EVSES):
        if request_index > 0:
            cp._received_reserve_now.clear()

        await asyncio.wait_for(
            cp._received_reserve_now.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )

        # Validate ReserveNowRequest content
        assert cp._reserve_now_data is not None
        req_data = cp._reserve_now_data

        # evseId must be omitted
        assert req_data.get('evse_id') is None, \
            f"Request {request_index + 1}: Expected evseId to be omitted, got {req_data.get('evse_id')}"
        # connectorType must be omitted
        assert req_data.get('connector_type') is None, \
            f"Request {request_index + 1}: Expected connectorType to be omitted, got {req_data.get('connector_type')}"

        id_token = req_data['id_token']
        if isinstance(id_token, dict):
            assert id_token.get('id_token') == VALID_ID_TOKEN, \
                f"Request {request_index + 1}: Expected idToken={VALID_ID_TOKEN}, got {id_token.get('id_token')}"
            assert id_token.get('type') == VALID_ID_TOKEN_TYPE, \
                f"Request {request_index + 1}: Expected idToken.type={VALID_ID_TOKEN_TYPE}, got {id_token.get('type')}"

    # Step 3-4: CS notifies CSMS about the status change - Reserved (all connectors)
    # Note: This step will be executed after the last ReserveNowRequest has been sent from step 1.
    for evse_idx in range(CONFIGURED_NUMBER_OF_EVSES):
        current_evse_id = evse_idx + 1
        await cp.send_status_notification(
            connector_id=CONNECTOR_ID,
            status=ConnectorStatusEnumType.reserved,
            evse_id=current_evse_id,
        )

        event_data = [
            EventDataType(
                trigger=EventTriggerEnumType.delta,
                actual_value='Reserved',
                component=ComponentType(name='Connector', evse=EVSEType(id=current_evse_id, connector_id=CONNECTOR_ID)),
                variable=VariableType(name='AvailabilityState'),
                timestamp=now_iso(),
                event_id=current_evse_id,
                event_notification_type=EventNotificationEnumType.custom_monitor,
            )
        ]
        await cp.send_notify_event(data=event_data)

    logging.info("TC_H_14 completed successfully")
    start_task.cancel()
    await ws.close()
