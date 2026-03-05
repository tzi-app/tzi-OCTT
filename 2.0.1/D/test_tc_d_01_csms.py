"""
Test case name      Send Local Authorization List - Full
Test case Id        TC_D_01_CSMS
Use case Id(s)      D01
Requirement(s)      D01.FR.01, D01.FR.06, D01.FR.18

Requirement Details:
    D01.FR.01: SendLocalListRequest SHALL contain the type of update (updateType) and a version number (versionNumber) that the Charging Station MUST associate with the Local Authorization List after it has been updated.
    D01.FR.06: All IdTokens in the Local Authorization List SHALL be unique. No duplicate values are allowed.
    D01.FR.18: versionNumber in a SendLocalListRequest SHALL be greater than 0. In GetLocalListVersionResp onse the versionNumber = 0 has a special meaning: No Local List installed. So the value 0 should never be used.
System under test   CSMS

Description         The CSMS sends a Local Authorization List which a Charging Station can use
                    for the authorization of idTokens. The list MAY be either a full list to
                    replace the current list in the Charging Station or it MAY be a differential
                    list with updates to be applied to the current list in the Charging Station.

Purpose             To verify if the CSMS is able to send a Full Local Authorization List
                    according to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration
    CSMS must be configured to send a Full Local Authorization List to the Charging Station
    upon connection or when triggered. The list must contain at least one idToken entry.

    Environment variables (configured in pytest.ini or environment):
        CSMS_ADDRESS            - WebSocket address of the CSMS (e.g. ws://localhost:8081)
        BASIC_AUTH_CP           - Charge Point ID to use for the connection (e.g. CP_1)
        BASIC_AUTH_CP_PASSWORD  - Password for Basic Auth
        CSMS_ACTION_TIMEOUT     - Seconds to wait for CSMS to send SendLocalListRequest (default: 30)
        LOCAL_LIST_VERSION      - Version number the CS reports for GetLocalListVersion (default: 1)

Test Scenario
    1. CS connects and sends BootNotificationRequest
    2. CS responds to optional GetLocalListVersionRequest from CSMS with configured version
    3. CSMS sends SendLocalListRequest with updateType=Full
    4. CS responds with SendLocalListResponse(status=Accepted)

Tool validations
    Step 3: Message SendLocalListRequest
        - updateType = Full
        - versionNumber > 0
        - localAuthorizationList is not empty
        - localAuthorizationList[n].idTokenInfo is not empty
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
    UpdateEnumType,
    SendLocalListStatusEnumType,
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
async def test_tc_d_01():
    """Send Local Authorization List - Full: CSMS sends a full local auth list."""
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
    cp._send_local_list_response_status = SendLocalListStatusEnumType.accepted
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Trigger CSMS to send SendLocalListRequest with updateType=Full
    trigger_task = asyncio.create_task(send_call(cp_id, "SendLocalList", {
        "versionNumber": LOCAL_LIST_VERSION + 1,
        "updateType": "Full",
        "localAuthorizationList": [
            {
                "idToken": {"idToken": "D001001", "type": "Central"},
                "idTokenInfo": {"status": "Accepted"}
            },
            {
                "idToken": {"idToken": "D001002", "type": "Central"},
                "idTokenInfo": {"status": "Accepted"}
            },
        ]
    }))

    await asyncio.wait_for(
        cp._received_send_local_list.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task

    data = cp._send_local_list_data
    assert data is not None, "No SendLocalListRequest received"

    assert data['update_type'] == UpdateEnumType.full, \
        f"Expected updateType=Full, got: {data['update_type']}"

    assert data['version_number'] > 0, \
        f"Expected versionNumber > 0, got: {data['version_number']}"

    assert len(data['local_authorization_list']) > 0, \
        "Expected non-empty localAuthorizationList for Full update"

    # Per spec: localAuthorizationList[n].idTokenInfo must not be empty
    for i, entry in enumerate(data['local_authorization_list']):
        if isinstance(entry, dict):
            id_token_info = entry.get('id_token_info') or entry.get('idTokenInfo')
        else:
            id_token_info = getattr(entry, 'id_token_info', None)

        assert id_token_info is not None, \
            f"Entry {i} must include idTokenInfo for Full update"

    logging.info(
        f"SendLocalListRequest validated: updateType=Full, "
        f"versionNumber={data['version_number']}, "
        f"entries={len(data['local_authorization_list'])}"
    )

    start_task.cancel()
    await ws.close()
