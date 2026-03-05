"""
Test case name      Send Local Authorization List - Full with empty list
Test case Id        TC_D_04_CSMS
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

Purpose             To verify if the CSMS is able to send a Full Local Authorization List without
                    data (empty list) according to the mechanism as described in the OCPP
                    specification. Sending a Full update with an empty list effectively clears all
                    authorization entries from the Charging Station's local list.

Prerequisite(s)     N/a

Configuration
    CSMS must be configured to send a Full Local Authorization List with no (zero)
    AuthorizationData elements in the message. This clears the local authorization list on
    the Charging Station.

    Environment variables (configured in pytest.ini or environment):
        CSMS_ADDRESS            - WebSocket address of the CSMS (e.g. ws://localhost:8081)
        BASIC_AUTH_CP           - Charge Point ID to use for the connection (e.g. CP_1)
        BASIC_AUTH_CP_PASSWORD  - Password for Basic Auth
        CSMS_ACTION_TIMEOUT     - Seconds to wait for CSMS to send SendLocalListRequest (default: 30)
        LOCAL_LIST_VERSION      - Version number the CS reports for GetLocalListVersion (default: 1)

Test Scenario
    1. CS connects and sends BootNotificationRequest
    2. CSMS sends SendLocalListRequest with updateType=Full and empty localAuthorizationList
    3. CS responds with SendLocalListResponse(status=Accepted)

Tool validations
    Step 2: Message SendLocalListRequest
        - updateType = Full
        - localAuthorizationList is absent or empty
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
async def test_tc_d_04():
    """Send Local Authorization List - Full with empty list: CSMS sends Full update with no entries."""
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

    # Trigger CSMS to send SendLocalListRequest with Full update and no list
    # (omit localAuthorizationList entirely — empty array violates OCPP schema minItems:1)
    trigger_task = asyncio.create_task(send_call(cp_id, "SendLocalList", {
        "versionNumber": LOCAL_LIST_VERSION + 1,
        "updateType": "Full",
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

    # For a Full update with empty list, localAuthorizationList must be absent or empty
    auth_list = data['local_authorization_list']
    assert len(auth_list) == 0, \
        (f"Expected empty localAuthorizationList for Full update with empty list, "
         f"got {len(auth_list)} entries")

    logging.info(
        f"SendLocalListRequest validated: updateType=Full, "
        f"versionNumber={data['version_number']}, "
        f"localAuthorizationList is empty (clears all entries)"
    )

    start_task.cancel()
    await ws.close()
