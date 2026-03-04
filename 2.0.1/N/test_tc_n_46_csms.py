"""
TC_N_46 - Clear Customer Information - Update Local Authorization List
Use case: N10 | Requirements: N10.FR.02, N10.FR.08, D01.FR.01, D01.FR.06, D01.FR.18
N10.FR.02: When the Customer referred to by the customer identifier is present in the Local Authorization List of a Charging Station The CSMS SHALL update the Local Authorization List using the SendLocalListRequest (see D01 - Send Local Authorization List). To prevent problems with Local Authorization List versions.
    Precondition: When the Customer referred to by the customer identifier is present in the Local Authorization List of a Charging Station
N10.FR.08: The CSMS SHALL include a reference to a customer by including either an idToken, customerCertificate or customerIdentifier in the CustomerInformationRequest.
D01.FR.01: SendLocalListRequest SHALL contain the type of update (updateType) and a version number (versionNumber) that the Charging Station MUST associate with the Local Authorization List after it has been updated.
D01.FR.06: All IdTokens in the Local Authorization List SHALL be unique. No duplicate values are allowed.
D01.FR.18: versionNumber in a SendLocalListRequest SHALL be greater than 0. In GetLocalListVersionResp onse the versionNumber = 0 has a special meaning: No Local List installed. So the value 0 should never be used.
System under test: CSMS

Description:
    CSMS sends a CustomerInformationRequest to clear and report customer information
    for a given idToken. The Charging Station responds with Accepted and sends
    NotifyCustomerInformation. Then the CSMS sends a SendLocalListRequest to update
    the local authorization list with a differential update.

Prerequisites:
    Local authorization list with <configured valid_idtoken_idtoken> is configured.

Purpose:
    To verify that the CSMS supports sending a CustomerInformationRequest with
    report=true, clear=true and a valid idToken, and then sends a SendLocalListRequest
    with updateType=Differential to update the local authorization list.

Main:
    1. CSMS sends CustomerInformationRequest (report=true, clear=true,
       idToken.idToken=<configured>, idToken.type=<configured>)
    2. OCTT responds CustomerInformationResponse (status = Accepted)
    3. OCTT sends NotifyCustomerInformationRequest
    4. CSMS responds NotifyCustomerInformationResponse
    5. CSMS sends SendLocalListRequest (updateType=Differential,
       versionNumber=<configured>+1, localAuthorizationList with the token)
    6. OCTT responds SendLocalListResponse with status = Accepted

Tool validations:
    * Step 1: report = true, clear = true,
              idToken.idToken = <configured>, idToken.type = <configured>
    * Step 5: updateType = Differential, versionNumber = <configured>+1,
              localAuthorizationList[0].idToken contains the configured values,
              idTokenInfo is omitted

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
    VALID_ID_TOKEN            - Valid idToken value (default 100000C01)
    VALID_ID_TOKEN_TYPE       - Valid idToken type (default Central)
    LOCAL_LIST_VERSION        - Current local list version (default 1)
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
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, build_default_ssl_context
from trigger import send_call

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
LOCAL_LIST_VERSION = int(os.environ['LOCAL_LIST_VERSION'])


@pytest.mark.asyncio
async def test_tc_n_46():
    """Clear Customer Information - Update Local Authorization List."""
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

    # Set local list version so CSMS knows the current version
    cp._local_list_version = LOCAL_LIST_VERSION

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Trigger CSMS to send CustomerInformationRequest
    await send_call(cp_id, "CustomerInformation", {
        "requestId": 1,
        "report": True,
        "clear": True,
        "idToken": {"idToken": VALID_ID_TOKEN, "type": VALID_ID_TOKEN_TYPE},
    })

    # Step 1-2: Wait for CSMS to send CustomerInformationRequest
    await asyncio.wait_for(
        cp._received_customer_information.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    data = cp._customer_information_data
    assert data is not None, "CustomerInformationRequest data must be present"

    # Tool validation Step 1: report=true, clear=true
    assert data['report'] is True, f"Expected report=True, got {data['report']}"
    assert data['clear'] is True, f"Expected clear=True, got {data['clear']}"

    # Validate idToken
    id_token = data['id_token']
    assert id_token is not None, "idToken must be present"
    assert id_token.get('id_token') == VALID_ID_TOKEN, \
        f"Expected idToken.idToken={VALID_ID_TOKEN}, got {id_token.get('id_token')}"
    assert id_token.get('type') == VALID_ID_TOKEN_TYPE, \
        f"Expected idToken.type={VALID_ID_TOKEN_TYPE}, got {id_token.get('type')}"

    request_id = data['request_id']

    logging.info("TC_N_46 step 1-2 completed: CustomerInformationResponse Accepted")

    # Step 3-4: OCTT sends NotifyCustomerInformationRequest
    await cp.send_notify_customer_information(
        data="Customer information data.",
        seq_no=0,
        request_id=request_id,
    )

    logging.info("TC_N_46 step 3-4 completed: NotifyCustomerInformation sent")

    # Trigger CSMS to send SendLocalListRequest
    await send_call(cp_id, "SendLocalList", {
        "versionNumber": LOCAL_LIST_VERSION + 1,
        "updateType": "Differential",
        "localAuthorizationList": [{
            "idToken": {"idToken": VALID_ID_TOKEN, "type": VALID_ID_TOKEN_TYPE},
        }],
    })

    # Step 5-6: Wait for CSMS to send SendLocalListRequest
    await asyncio.wait_for(
        cp._received_send_local_list.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    send_local_list_data = cp._send_local_list_data
    assert send_local_list_data is not None, "SendLocalListRequest data must be present"

    # Tool validation Step 5: updateType=Differential
    assert send_local_list_data['update_type'] == 'Differential', \
        f"Expected updateType=Differential, got {send_local_list_data['update_type']}"

    # Tool validation Step 5: versionNumber = configured + 1
    expected_version = LOCAL_LIST_VERSION + 1
    assert send_local_list_data['version_number'] == expected_version, \
        f"Expected versionNumber={expected_version}, got {send_local_list_data['version_number']}"

    # Tool validation Step 5: localAuthorizationList[0].idToken contains configured values
    auth_list = send_local_list_data['local_authorization_list']
    assert auth_list is not None and len(auth_list) > 0, \
        "localAuthorizationList must contain at least one entry"

    first_entry = auth_list[0]
    entry_id_token = first_entry.get('id_token', {})
    assert entry_id_token.get('id_token') == VALID_ID_TOKEN, \
        f"Expected localAuthorizationList[0].idToken.idToken={VALID_ID_TOKEN}, " \
        f"got {entry_id_token.get('id_token')}"
    assert entry_id_token.get('type') == VALID_ID_TOKEN_TYPE, \
        f"Expected localAuthorizationList[0].idToken.type={VALID_ID_TOKEN_TYPE}, " \
        f"got {entry_id_token.get('type')}"

    # Tool validation Step 5: idTokenInfo is omitted
    assert first_entry.get('id_token_info') is None, \
        f"Expected idTokenInfo to be omitted, got {first_entry.get('id_token_info')}"

    logging.info(f"TC_N_46 step 5-6 completed: SendLocalListRequest received "
                 f"(Differential, version={send_local_list_data['version_number']})")

    logging.info("TC_N_46 completed successfully")
    start_task.cancel()
    await ws.close()
