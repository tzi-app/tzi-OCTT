"""
TC_M_19 - Retrieve certificates from Charging Station - No matching certificate found
Use case: M03 | Requirements: M03.FR.01, M03.FR.02
M03.FR.01: After receiving a GetInstalledCertificateIdsRequest The Charging Station SHALL respond with a GetInstalledCertificateIdsResponse.
    Precondition: After receiving a GetInstalledCertificateIdsRequest
M03.FR.02: M03.FR.01 AND No certificate matching certificateType was found. The Charging Station SHALL respond with status NotFound.
    Precondition: M03.FR.01 AND No certificate matching certificateType was found
System under test: CSMS

Description:
    The CSMS is able to retrieve the certificates installed at the Charging Station using the
    GetInstalledCertificateIdsRequest message.

Purpose:
    To verify if the CSMS is able to handle a response from the Charging Station indicating it was
    not able to find a certificate for the requested criteria.

Main:
    Manual Action: Trigger the CSMS to send a GetInstalledCertificateIdsRequest with certificateType
    ManufacturerRootCertificate.
    1. The CSMS sends a GetInstalledCertificateIdsRequest
    2. The OCTT responds with a GetInstalledCertificateIdsResponse
       with status = NotFound
       certificateHashDataChain is omitted.

Tool validations:
    * Step 1: GetInstalledCertificateIdsRequest
      - certificateType is ManufacturerRootCertificate

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
    GetCertificateIdUseEnumType,
    GetInstalledCertificateStatusEnumType,
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
async def test_tc_m_19():
    """Retrieve certificates from Charging Station - No matching certificate found."""
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
    # Configure CS to respond with NotFound and no chain
    cp._get_installed_certificate_ids_response_status = GetInstalledCertificateStatusEnumType.notFound
    cp._get_installed_certificate_ids_response_chain = None
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1: Wait for CSMS to send GetInstalledCertificateIdsRequest
    await asyncio.wait_for(
        cp._received_get_installed_certificate_ids.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate request content
    assert cp._get_installed_certificate_ids_data is not None

    # Tool validation: certificateType is ManufacturerRootCertificate
    cert_type = cp._get_installed_certificate_ids_data['certificate_type']
    assert cert_type is not None, "certificateType must be present"
    if isinstance(cert_type, list):
        assert GetCertificateIdUseEnumType.manufacturer_root_certificate in cert_type, \
            f"Expected ManufacturerRootCertificate in list, got {cert_type}"
    else:
        assert cert_type == GetCertificateIdUseEnumType.manufacturer_root_certificate, \
            f"Expected ManufacturerRootCertificate, got {cert_type}"

    # CS responded with NotFound and no chain (configured before start)

    logging.info("TC_M_19 completed successfully")
    start_task.cancel()
    await ws.close()
