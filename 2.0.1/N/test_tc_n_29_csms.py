"""
TC_N_29 - Get Customer Information - Not Accepted
Use case: N09 | Requirements: N09.FR.01, N09.FR.04
N09.FR.01: When the CSMS wants to retrieve CustomerInformation from the Charging Station. The report flag in the CustomerInformationRequest SHALL be set to true.
    Precondition: When the CSMS wants to retrieve CustomerInformation from the Charging Station.
N09.FR.04: The CSMS SHALL include a reference to a customer by including either an idToken, customerCertificate or customerIdentifier in the CustomerInformationRequest.
System under test: CSMS

Description:
    The CSMS sends a message to the Charging Station to retrieve IdToken customer information.
    The Charging Station rejects the request.

Purpose:
    To verify if the CSMS is able to handle a CustomerInformationResponse with status = Rejected.

Main:
    1. CSMS sends CustomerInformationRequest with report=true,
       idToken.idToken=<valid>, idToken.type=<valid>
    2. OCTT responds CustomerInformationResponse with status = Rejected

Tool validations:
    * Step 1: report = true,
              idToken.idToken = <Configured valid_idtoken_idtoken>,
              idToken.type = <Configured valid_idtoken_type>

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
    CustomerInformationStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']


@pytest.mark.asyncio
async def test_tc_n_29():
    """Get Customer Information - Not Accepted."""
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

    # Configure handler to respond with Rejected BEFORE starting
    cp._customer_information_response_status = CustomerInformationStatusEnumType.rejected

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1-2: Wait for CSMS to send CustomerInformationRequest
    await asyncio.wait_for(
        cp._received_customer_information.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    data = cp._customer_information_data
    assert data is not None, "CustomerInformationRequest data must be present"

    # Validate report=true
    assert data['report'] is True, f"Expected report=True, got {data['report']}"

    # Validate idToken
    id_token = data['id_token']
    assert id_token is not None, "idToken must be present"
    assert id_token.get('id_token') == VALID_ID_TOKEN, \
        f"Expected idToken.idToken={VALID_ID_TOKEN}, got {id_token.get('id_token')}"
    assert id_token.get('type') == VALID_ID_TOKEN_TYPE, \
        f"Expected idToken.type={VALID_ID_TOKEN_TYPE}, got {id_token.get('type')}"

    logging.info("TC_N_29 completed successfully: CustomerInformationResponse Rejected")

    # No NotifyCustomerInformation is sent (CS rejected the request)

    start_task.cancel()
    await ws.close()
