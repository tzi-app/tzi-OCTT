"""
TC_M_03 - Install CA certificate - V2GRootCertificate
Use case: M05 | Requirements: M05.FR.01
M05.FR.01: After receiving an InstallCertificateRequest The Charging Station SHALL attempt to install the certificate and respond with an InstallCertificateResponse.
    Precondition: After receiving an InstallCertificateRequest
System under test: CSMS

Description:
    The CSMS is able to request the Charging Station to install new Root CA certificates using the
    InstallCertificateRequest message.

Purpose:
    To verify if the CSMS is able to request a Charging Station to install a new V2GRootCertificate.

Main:
    1. Execute Reusable State CertificateInstalled for certificateType V2GRootCertificate.

Tool validations:
    N/a

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


@pytest.mark.asyncio
async def test_tc_m_03():
    """Install CA certificate - V2GRootCertificate."""
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

    # Step 1: Trigger CSMS to send InstallCertificateRequest
    async def trigger_install_cert():
        await asyncio.sleep(1)
        await send_call(cp_id, "InstallCertificate", {
            "certificateType": "V2GRootCertificate",
            "certificate": "MIICaTCCAdKgAwIBAgIUXzo...",
        })
    trigger_task = asyncio.create_task(trigger_install_cert())
    await asyncio.wait_for(
        cp._received_install_certificate.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    # Validate InstallCertificateRequest content
    assert cp._install_certificate_data is not None
    cert_type = cp._install_certificate_data['certificate_type']
    certificate = cp._install_certificate_data['certificate']

    # Tool validation: certificateType must be V2GRootCertificate
    assert cert_type == InstallCertificateUseEnumType.v2g_root_certificate, \
        f"Expected certificateType=V2GRootCertificate, got {cert_type}"

    # Tool validation: certificate must be present
    assert certificate is not None and len(certificate) > 0, \
        "certificate must be present in InstallCertificateRequest"

    logging.info("TC_M_03 completed successfully")
    start_task.cancel()
    await ws.close()
