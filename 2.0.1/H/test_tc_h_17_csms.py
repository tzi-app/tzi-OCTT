"""
TC_H_17 - Cancel reservation of an EVSE - Success
Use case: H02 | Requirements: N/a
System under test: CSMS

Description:
    The CSMS is able to cancel a reservation by sending a CancelReservationRequest to the Charging
    Station.

Purpose:
    To verify if the CSMS is able to request the Charging Station to cancel a reservation, by sending a
    CancelReservationRequest.

Main:
    Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific EVSE.
    1. The CSMS sends a ReserveNowRequest
    2. CS responds with ReserveNowResponse (status=Accepted)
    3. CS notifies CSMS (StatusNotificationRequest connectorStatus=Reserved + NotifyEventRequest)
    4. The CSMS responds accordingly.
    Manual Action: Trigger the CSMS to send a CancelReservationRequest for the reservation created at step 1.
    5. The CSMS sends a CancelReservationRequest
    6. CS responds with CancelReservationResponse (status=Accepted)
    7. CS notifies CSMS (StatusNotificationRequest connectorStatus=Available + NotifyEventRequest)
    8. The CSMS responds accordingly.

Tool validations:
    * Step 1: ReserveNowRequest
      - evseId must be <Configured evseId>
      - connectorType must be omitted
      - idToken.idToken <Configured valid_idtoken_idtoken>
      - idToken.type <Configured valid_idtoken_type>
    * Step 5: CancelReservationRequest
      - reservationId must be equal to the id provided at step 1

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
    VALID_ID_TOKEN            - Valid idToken value
    VALID_ID_TOKEN_TYPE       - Valid idToken type
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


@pytest.mark.asyncio
async def test_tc_h_17():
    """Cancel reservation of an EVSE - Success."""
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

    assert req_data['evse_id'] == EVSE_ID, \
        f"Expected evseId={EVSE_ID}, got {req_data['evse_id']}"
    assert req_data.get('connector_type') is None, \
        f"Expected connectorType to be omitted, got {req_data.get('connector_type')}"

    id_token = req_data['id_token']
    if isinstance(id_token, dict):
        assert id_token.get('id_token') == VALID_ID_TOKEN, \
            f"Expected idToken={VALID_ID_TOKEN}, got {id_token.get('id_token')}"
        assert id_token.get('type') == VALID_ID_TOKEN_TYPE, \
            f"Expected idToken.type={VALID_ID_TOKEN_TYPE}, got {id_token.get('type')}"

    reservation_id = req_data['id']

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

    # Step 5-6: Wait for CSMS to send CancelReservationRequest
    await asyncio.wait_for(
        cp._received_cancel_reservation.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate CancelReservationRequest content
    assert cp._cancel_reservation_data is not None
    cancel_data = cp._cancel_reservation_data
    assert cancel_data['reservation_id'] == reservation_id, \
        f"Expected reservationId={reservation_id}, got {cancel_data['reservation_id']}"

    # CS responded with Accepted (handled by on_cancel_reservation handler)

    # Step 7-8: CS notifies CSMS about the status change - Available
    await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusEnumType.available,
        evse_id=EVSE_ID,
    )

    event_data = [
        EventDataType(
            trigger=EventTriggerEnumType.delta,
            actual_value='Available',
            component=ComponentType(name='Connector', evse=EVSEType(id=EVSE_ID, connector_id=CONNECTOR_ID)),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=EVSE_ID,
            event_notification_type=EventNotificationEnumType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)

    logging.info("TC_H_17 completed successfully")
    start_task.cancel()
    await ws.close()
