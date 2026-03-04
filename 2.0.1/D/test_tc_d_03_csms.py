"""
Test case name      Send Local Authorization List - Differential Remove
Test case Id        TC_D_03_CSMS
Use case Id(s)      D01
Requirement(s)      D01.FR.01, D01.FR.06, D01.FR.17, D01.FR.18

Requirement Details:
    D01.FR.01: SendLocalListRequest SHALL contain the type of update (updateType) and a version number (versionNumber) that the Charging Station MUST associate with the Local Authorization List after it has been updated.
    D01.FR.06: All IdTokens in the Local Authorization List SHALL be unique. No duplicate values are allowed.
    D01.FR.17: If the Charging Station receives a SendLocalListRequest with updateType is Differential AND localAuthorizationList contains AuthorizationData elements without idTokenInfo The Charging Station SHALL remove these elements from its Local Authorization List and set the version number to the value specified in the message.
        Precondition: If the Charging Station receives a SendLocalListRequest with updateType is Differential AND localAuthorizationList contains AuthorizationData elements without idTokenInfo
    D01.FR.18: versionNumber in a SendLocalListRequest SHALL be greater than 0. In GetLocalListVersionResp onse the versionNumber = 0 has a special meaning: No Local List installed. So the value 0 should never be used.
System under test   CSMS

Description         The CSMS sends a Local Authorization List which a Charging Station can use
                    for the authorization of idTokens. The list MAY be either a full list to
                    replace the current list in the Charging Station or it MAY be a differential
                    list with updates to be applied to the current list in the Charging Station.

Purpose             To verify if the CSMS is able to send a Differential Local Authorization List
                    with AuthorizationData elements without idTokenInfo (signalling removal) according
                    to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration
    CSMS must be configured to send a Differential Local Authorization List where the entries
    contain only idToken fields (no idTokenInfo). According to D01.FR.17, an AuthorizationData
    entry without idTokenInfo signals that the corresponding idToken should be removed from the
    local authorization list on the Charging Station.

    The versionNumber in the SendLocalListRequest must be greater than the version currently
    reported by the CS.

    Environment variables (configured in pytest.ini or environment):
        CSMS_ADDRESS            - WebSocket address of the CSMS (e.g. ws://localhost:8081)
        BASIC_AUTH_CP           - Charge Point ID to use for the connection (e.g. CP_1)
        BASIC_AUTH_CP_PASSWORD  - Password for Basic Auth
        CSMS_ACTION_TIMEOUT     - Seconds to wait for CSMS to send SendLocalListRequest (default: 30)
        LOCAL_LIST_VERSION      - Version number the CS reports for GetLocalListVersion (default: 1).
                                  The CSMS must send a versionNumber strictly greater than this.

Test Scenario
    1. CS connects and sends BootNotificationRequest
    2. CSMS sends SendLocalListRequest with updateType=Differential and entries with idToken only
    3. CS responds with SendLocalListResponse(status=Accepted)

Tool validations
    Step 2: Message SendLocalListRequest
        - updateType = Differential
        - versionNumber > currently configured version in OCTT
        - localAuthorizationList entries contain idToken but NO idTokenInfo (removal semantics)
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
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
LOCAL_LIST_VERSION = int(os.environ['LOCAL_LIST_VERSION'])


@pytest.mark.asyncio
async def test_tc_d_03():
    """Send Local Authorization List - Differential Remove: entries have idToken but no idTokenInfo."""
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
    cp._local_list_version = LOCAL_LIST_VERSION
    cp._send_local_list_response_status = SendLocalListStatusEnumType.accepted
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Wait for CSMS to send SendLocalListRequest.
    # MockChargePoint handles any optional GetLocalListVersionRequest automatically.
    await asyncio.wait_for(
        cp._received_send_local_list.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    data = cp._send_local_list_data
    assert data is not None, "No SendLocalListRequest received"

    assert data['update_type'] == UpdateEnumType.differential, \
        f"Expected updateType=Differential, got: {data['update_type']}"

    assert data['version_number'] > LOCAL_LIST_VERSION, \
        (f"Expected versionNumber > {LOCAL_LIST_VERSION} (current version), "
         f"got: {data['version_number']}")

    auth_list = data['local_authorization_list']
    assert len(auth_list) > 0, \
        "Expected non-empty localAuthorizationList for Differential Remove"

    # Per D01.FR.17: entries without idTokenInfo signal removal from the local list.
    # Verify that all entries include idToken and omit idTokenInfo.
    for i, entry in enumerate(auth_list):
        if isinstance(entry, dict):
            id_token = entry.get('id_token') or entry.get('idToken')
            id_token_info = entry.get('id_token_info') or entry.get('idTokenInfo')
        else:
            id_token = getattr(entry, 'id_token', None)
            id_token_info = getattr(entry, 'id_token_info', None)

        assert id_token is not None, \
            f"Entry {i} must include idToken for removal semantics"

        assert id_token_info is None, \
            (f"Entry {i} should not have idTokenInfo (removal semantics), "
             f"but got: {id_token_info}")

    logging.info(
        f"SendLocalListRequest validated: updateType=Differential (remove), "
        f"versionNumber={data['version_number']}, "
        f"entries={len(auth_list)} (all without idTokenInfo)"
    )

    start_task.cancel()
    await ws.close()
