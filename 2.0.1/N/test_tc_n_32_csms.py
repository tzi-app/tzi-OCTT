"""
TC_N_32 - Clear Customer Information - Clear and no report
Use case: N10 | Requirements: N10.FR.08
N10.FR.08: The CSMS SHALL include a reference to a customer by including either an idToken, customerCertificate or customerIdentifier in the CustomerInformationRequest.
System under test: CSMS

Description:
    CSMS sends a message to the Charging Station to clear IdToken customer
    information with no report.

Purpose:
    To test that CSMS supports sending a CustomerInformationRequest with
    report=false, clear=true and a valid idToken. Even though report=false,
    the OCTT still sends NotifyCustomerInformation per the specification.

Main:
    1. CSMS sends CustomerInformationRequest (report=false, clear=true,
       idToken.idToken=<valid>, idToken.type=<valid>)
    2. OCTT responds CustomerInformationResponse (status = Accepted)
    3. OCTT sends NotifyCustomerInformationRequest
    4. CSMS responds NotifyCustomerInformationResponse

Tool validations:
    * Step 1: CustomerInformationRequest with report = false, clear = true,
              idToken.idToken = <valid>, idToken.type = <valid>

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
    VALID_ID_TOKEN            - Valid idToken value (default 100000C01)
    VALID_ID_TOKEN_TYPE       - Valid idToken type (default Central)
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


@pytest.mark.asyncio
async def test_tc_n_32():
    """Clear Customer Information - Clear and no report."""
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

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Trigger CSMS to send CustomerInformationRequest
    await send_call(cp_id, "CustomerInformation", {
        "requestId": 1,
        "report": False,
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

    # Validate report=false, clear=true
    assert data['report'] is False, f"Expected report=False, got {data['report']}"
    assert data['clear'] is True, f"Expected clear=True, got {data['clear']}"

    # Validate idToken
    id_token = data['id_token']
    assert id_token is not None, "idToken must be present"
    assert id_token.get('id_token') == VALID_ID_TOKEN, \
        f"Expected idToken.idToken={VALID_ID_TOKEN}, got {id_token.get('id_token')}"
    assert id_token.get('type') == VALID_ID_TOKEN_TYPE, \
        f"Expected idToken.type={VALID_ID_TOKEN_TYPE}, got {id_token.get('type')}"

    request_id = data['request_id']

    logging.info("TC_N_32 step 1-2 completed: CustomerInformationResponse Accepted")

    # Step 3-4: OCTT sends NotifyCustomerInformationRequest
    # Even though report=false, the OCTT still sends NotifyCustomerInformation per spec
    await cp.send_notify_customer_information(
        data="",
        seq_no=0,
        request_id=request_id,
    )

    logging.info("TC_N_32 completed successfully")
    start_task.cancel()
    await ws.close()
