"""
TC_H_22 - Reserve a specific EVSE - Configured to Reject
Use case: H01 | Requirements: N/a
System under test: CSMS

Description:
    The CSMS is able to reserve a specific EVSE for a specific IdToken by sending a ReserveNowRequest
    containing an evseId.

Purpose:
    To verify if the CSMS is able to correctly read the respond from a charging station when it is
    configured not to accept reservations.

Main:
    Manual Action: Trigger the CSMS to send a ReserveNowRequest.
    1. The CSMS sends a ReserveNowRequest
    2. CS responds with ReserveNowResponse (status=Rejected)

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
    ReserveNowStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, build_default_ssl_context
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


@pytest.mark.asyncio
async def test_tc_h_22():
    """Reserve a specific EVSE - Configured to Reject."""
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
    # Configure CS to reject reservations
    cp._reserve_now_response_status = ReserveNowStatusEnumType.rejected
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available, evse_id=EVSE_ID)

    # Step 1-2: Trigger CSMS to send ReserveNowRequest
    async def trigger_reserve_now():
        await asyncio.sleep(1)
        from datetime import datetime, timezone, timedelta
        expiry = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()
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

    # CS responded with Rejected (configured before start)
    assert cp._reserve_now_data is not None

    logging.info("TC_H_22 completed successfully")
    start_task.cancel()
    await ws.close()
