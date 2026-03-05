"""
TC_M_26 - Certificate Installation EV - Success
Use case: M01 | Requirements: M01.FR.01
M01.FR.01: Upon receiving an ISO 15118 CertificateInstallationReq The Charging Station SHALL forward the request to the CSMS using the Get15118EVCertificateRequest message with action = Install. The CSMS is responsible for forwarding it to the secondary actor which will process the CertificateUpdateRequest. This could
    Precondition: Upon receiving an ISO 15118 CertificateInstallationReq message with action = Install.
System under test: CSMS

Description:
    The EV initiates installing a new certificate. The Charging Station forwards the request for
    a new certificate to the CSMS.

Purpose:
    To verify if the CSMS is able to return the Raw CertificateInstallationRes response for the
    EV to the Charging Station.

Main:
    1. The OCTT sends a Get15118EVCertificateRequest with action = Install
    2. The CSMS responds with a Get15118EVCertificateResponse

Tool validations:
    * Step 2: Get15118EVCertificateResponse
      - status = Accepted
      - exiResponse = <Raw CertificateInstallationRes response for the EV, Base64 encoded>

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
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
    CertificateActionEnumType,
    Iso15118EVCertificateStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, build_default_ssl_context
from mock_cps_proxy import MockCpsProxy

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])

CPS_PROXY_PORT = 19081


@pytest.mark.asyncio
async def test_tc_m_26():
    """Certificate Installation EV - Success."""
    cps_proxy = MockCpsProxy(port=CPS_PROXY_PORT)
    cps_proxy.start()

    try:
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

        # Step 1: CS sends Get15118EVCertificateRequest with action = Install
        response = await cp.send_get_15118_ev_certificate_request(
            iso15118_schema_version='urn:iso:15118:2:2013:MsgDef',
            action=CertificateActionEnumType.install,
            exi_request='dGVzdEVYSVJlcXVlc3REYXRh',  # Base64 encoded test data
        )

        # Tool validation Step 2: status must be Accepted
        assert response.status == Iso15118EVCertificateStatusEnumType.accepted, \
            f"Expected Get15118EVCertificateResponse status=Accepted, got {response.status}"

        # Tool validation Step 2: exiResponse must be present
        assert response.exi_response is not None and len(response.exi_response) > 0, \
            "exiResponse must be present in Get15118EVCertificateResponse"

        logging.info("TC_M_26 completed successfully")
        start_task.cancel()
        await ws.close()
    finally:
        cps_proxy.stop()
