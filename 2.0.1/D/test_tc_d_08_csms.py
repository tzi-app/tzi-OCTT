"""
Test case name      Get Local List Version - Success
Test case Id        TC_D_08_CSMS
Use case Id(s)      D02
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS can request a Charging Station for the version number of the Local
                    Authorization List by sending a GetLocalListVersionRequest.

Purpose             To verify if the CSMS is able to request the Local Authorization List version
                    according to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration
    CSMS must be configured to send a GetLocalListVersionRequest to the Charging Station
    upon connection or when triggered. The CS (OCTT) is configured to respond with a
    specific version number (LOCAL_LIST_VERSION).

    Environment variables (configured in pytest.ini or environment):
        CSMS_ADDRESS            - WebSocket address of the CSMS (e.g. ws://localhost:8081)
        BASIC_AUTH_CP           - Charge Point ID to use for the connection (e.g. CP_1)
        BASIC_AUTH_CP_PASSWORD  - Password for Basic Auth
        CSMS_ACTION_TIMEOUT     - Seconds to wait for CSMS to send GetLocalListVersionRequest (default: 30)
        LOCAL_LIST_VERSION      - Version number the CS reports in GetLocalListVersionResponse (default: 1).
                                  The CSMS should accept any non-negative integer as the version.

Test Scenario
    1. CS connects and sends BootNotificationRequest
    2. CSMS sends GetLocalListVersionRequest
    3. CS responds with GetLocalListVersionResponse(versionNumber=LOCAL_LIST_VERSION)

Tool validations
    No specific content validations on GetLocalListVersionRequest (no required fields).
    Post scenario: The CSMS must have correctly received the version number from the CS.
"""

import asyncio
import pytest
import os
import time
import logging

import websockets
from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from trigger import send_call
from utils import get_basic_auth_headers, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
LOCAL_LIST_VERSION = int(os.environ['LOCAL_LIST_VERSION'])


@pytest.mark.asyncio
async def test_tc_d_08():
    """Get Local List Version - Success: CSMS requests local list version, CS responds with configured version."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ssl_ctx = build_default_ssl_context() if uri.startswith('wss://') else None
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    cp._local_list_version = LOCAL_LIST_VERSION
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Trigger CSMS to send GetLocalListVersionRequest
    trigger_task = asyncio.create_task(send_call(cp_id, "GetLocalListVersion", {}))

    await asyncio.wait_for(
        cp._received_get_local_list_version.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task

    # The MockChargePoint handler automatically responds with LOCAL_LIST_VERSION.
    # We verify the CSMS actually sent the request (event was set).
    assert cp._received_get_local_list_version.is_set(), \
        "GetLocalListVersionRequest was not received from CSMS"

    logging.info(
        f"GetLocalListVersionRequest received and responded with versionNumber={LOCAL_LIST_VERSION}"
    )

    start_task.cancel()
    await ws.close()
