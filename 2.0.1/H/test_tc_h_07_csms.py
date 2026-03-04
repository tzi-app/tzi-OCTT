"""
TC_H_07 - Reserve a specific EVSE - Reservation Ended / not used
Use case: H01(S2), H04 | Requirements: N/a
System under test: CSMS

Description:
    The CSMS is able to reserve a specific EVSE for a specific IdToken by sending a ReserveNowRequest
    containing an evseId.

Purpose:
    To verify if the CSMS is able to handle a reservation that is canceled by the Charging Station,
    because the EV driver did not arrive before the set expiryDateTime was reached.

Main:
    Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific EVSE.
    1. The CSMS sends a ReserveNowRequest with expiryDateTime = current time + configured transaction duration
    2. CS responds with ReserveNowResponse (status=Accepted)
    3. CS notifies CSMS (StatusNotificationRequest connectorStatus=Reserved + NotifyEventRequest)
    4. The CSMS responds accordingly.
    5. CS notifies CSMS (StatusNotificationRequest connectorStatus=Available + NotifyEventRequest)
    6. The CSMS responds accordingly.
    Note: Wait until expiryDateTime from step 1 expires
    7. CS sends ReservationStatusUpdateRequest (reservationUpdateStatus=Expired, reservationId=<id from step 1>)
    8. The CSMS responds with ReservationStatusUpdateResponse

Tool validations:
    * Step 1: ReserveNowRequest
      - evseId must be <Configured evseId>
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
    TRANSACTION_DURATION      - Duration for reservation expiry in seconds (default 5)
"""
import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    ReservationUpdateStatusEnumType,
    EventTriggerEnumType,
    EventNotificationEnumType,
)
from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType, EVSEType

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
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


@pytest.mark.asyncio
async def test_tc_h_07():
    """Reserve a specific EVSE - Reservation Ended / not used."""
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

    # Step 1-2: Trigger CSMS to send ReserveNowRequest
    async def trigger_reserve_now():
        await asyncio.sleep(1)
        expiry = (datetime.now(timezone.utc) + timedelta(seconds=TRANSACTION_DURATION)).isoformat()
        await send_call(BASIC_AUTH_CP, "ReserveNow", {
            "id": 1,
            "expiryDateTime": expiry,
            "idToken": {"idToken": VALID_ID_TOKEN, "type": VALID_ID_TOKEN_TYPE},
            "evseId": EVSE_ID,
        })

    trigger_task = asyncio.create_task(trigger_reserve_now())

    await asyncio.wait_for(
        cp._received_reserve_now.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

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
    expiry_date_time = req_data['expiry_date_time']
    assert expiry_date_time is not None, "Expected expiryDateTime to be provided"

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

    # Note: Wait until the provided expiryDateTime from step 1 expires before step 5
    # Validate and parse expiry time from ReserveNowRequest
    try:
        expiry_dt = datetime.fromisoformat(expiry_date_time.replace('Z', '+00:00'))
        if expiry_dt.tzinfo is None:
            expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)

        now_dt = datetime.now(timezone.utc)
        initial_wait_seconds = (expiry_dt - now_dt).total_seconds()
        assert initial_wait_seconds > 0, \
            f"Expected expiryDateTime in the future, got delta={initial_wait_seconds:.2f}s"

        # Keep a broad tolerance because test system and CSMS clocks may drift.
        tolerance = max(10, TRANSACTION_DURATION)
        assert abs(initial_wait_seconds - TRANSACTION_DURATION) <= tolerance, \
            f"Expected expiryDateTime around now+{TRANSACTION_DURATION}s, got delta={initial_wait_seconds:.2f}s"

        wait_seconds = max(0, initial_wait_seconds)
        await asyncio.sleep(wait_seconds + 1)
    except (ValueError, TypeError):
        # Fallback: wait for TRANSACTION_DURATION
        await asyncio.sleep(TRANSACTION_DURATION + 1)

    # Step 5-6: CS notifies CSMS about the status change back to Available
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

    # Step 7-8: CS sends ReservationStatusUpdateRequest (Expired)
    response = await cp.send_reservation_status_update(
        reservation_id=reservation_id,
        reservation_update_status=ReservationUpdateStatusEnumType.expired,
    )
    assert response is not None

    logging.info("TC_H_07 completed successfully")
    start_task.cancel()
    await ws.close()
