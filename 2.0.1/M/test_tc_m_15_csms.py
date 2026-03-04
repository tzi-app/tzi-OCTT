"""
TC_M_15 - Retrieve certificates from Charging Station - V2GCertificateChain
Use case: M03 | Requirements: M03.FR.01, M03.FR.05
M03.FR.01: After receiving a GetInstalledCertificateIdsRequest The Charging Station SHALL respond with a GetInstalledCertificateIdsResponse.
    Precondition: After receiving a GetInstalledCertificateIdsRequest
M03.FR.05: When the Charging Station receives a GetInstalledCertificateIdsRequest with certificateType V2GCertificateChain, the Charging Station SHALL include the hash data for each installed certificate belonging to a V2G certificate chain. Sub CA certificates SHALL be placed as a childCertificate under the V2G Charging Station certificate.
    Precondition: When the Charging Station receives a GetInstalledCertificateIdsRequest with certificateType V2GCertificateChain
System under test: CSMS

Description:
    The CSMS is able to retrieve the certificates installed at the Charging Station using the
    GetInstalledCertificateIdsRequest message.

Purpose:
    To verify if the CSMS is able to retrieve the hashData from all certificates that are part of a
    V2GCertificateChain stored at the Charging Station.

Main:
    1. Execute Reusable State GetInstalledCertificates for certificateType V2GCertificateChain.

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
    GetCertificateIdUseEnumType,
    GetInstalledCertificateStatusEnumType,
    HashAlgorithmEnumType,
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
async def test_tc_m_15():
    """Retrieve certificates from Charging Station - V2GCertificateChain."""
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
    cp._get_installed_certificate_ids_response_status = GetInstalledCertificateStatusEnumType.accepted
    cp._get_installed_certificate_ids_response_chain = [{
        'certificate_type': GetCertificateIdUseEnumType.v2g_certificate_chain,
        'certificate_hash_data': {
            'hash_algorithm': HashAlgorithmEnumType.sha256,
            'issuer_name_hash': 'aabbccdd' * 8,
            'issuer_key_hash': 'eeff0011' * 8,
            'serial_number': '01020304',
        },
        'child_certificate_hash_data': [{
            'hash_algorithm': HashAlgorithmEnumType.sha256,
            'issuer_name_hash': '11223344' * 8,
            'issuer_key_hash': '55667788' * 8,
            'serial_number': '05060708',
        }],
    }]
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
    cert_type = cp._get_installed_certificate_ids_data['certificate_type']
    assert cert_type is not None, "certificateType must be present"

    if isinstance(cert_type, list):
        assert GetCertificateIdUseEnumType.v2g_certificate_chain in cert_type, \
            f"Expected V2GCertificateChain in certificateType list, got {cert_type}"
    else:
        assert cert_type == GetCertificateIdUseEnumType.v2g_certificate_chain, \
            f"Expected V2GCertificateChain, got {cert_type}"

    logging.info("TC_M_15 completed successfully")
    start_task.cancel()
    await ws.close()
