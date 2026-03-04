"""
TC_M_05 - Install CA certificate - Failed
Use case: M05 | Requirements: M05.FR.01, M05.FR.03
M05.FR.01: After receiving an InstallCertificateRequest The Charging Station SHALL attempt to install the certificate and respond with an InstallCertificateResponse.
    Precondition: After receiving an InstallCertificateRequest
M05.FR.03: M05.FR.01 AND The installation failed. The Charging Station SHALL respond with InstallCertificateResponse with status Failed.
    Precondition: M05.FR.01 AND The installation failed
System under test: CSMS

Description:
    The CSMS is able to request the Charging Station to install new Root CA certificates using the
    InstallCertificateRequest message.

Purpose:
    To verify if the CSMS is able to handle a Charging Station reporting it failed to install the
    requested certificate.

Main:
    Manual Action: Trigger the CSMS to send an InstallCertificateRequest with certificateType
    CSMSRootCertificate.
    1. The CSMS sends an InstallCertificateRequest
    2. The OCTT responds with an InstallCertificateResponse with status = Failed

Tool validations:
    * Step 1: InstallCertificateRequest
      - certificateType must be CSMSRootCertificate
      - certificate contains <A certificate>

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
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
    InstallCertificateUseEnumType,
    InstallCertificateStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_m_05():
    """Install CA certificate - Failed."""
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
    # Configure CS to respond with Failed
    cp._install_certificate_response_status = InstallCertificateStatusEnumType.failed
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1: Wait for CSMS to send InstallCertificateRequest
    await asyncio.wait_for(
        cp._received_install_certificate.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate InstallCertificateRequest was received
    assert cp._install_certificate_data is not None
    cert_type = cp._install_certificate_data['certificate_type']
    certificate = cp._install_certificate_data['certificate']

    # Tool validation: certificateType must be CSMSRootCertificate
    assert cert_type == InstallCertificateUseEnumType.csms_root_certificate, \
        f"Expected certificateType=CSMSRootCertificate, got {cert_type}"

    # Tool validation: certificate must be present
    assert certificate is not None and len(certificate) > 0, \
        "certificate must contain a certificate"

    # CS responded with Failed (configured before start)

    logging.info("TC_M_05 completed successfully")
    start_task.cancel()
    await ws.close()
