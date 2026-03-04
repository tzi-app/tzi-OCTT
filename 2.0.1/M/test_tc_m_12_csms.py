"""
TC_M_12 - Retrieve certificates from Charging Station - CSMSRootCertificate
Use case: M03 | Requirements: M03.FR.01
M03.FR.01: After receiving a GetInstalledCertificateIdsRequest The Charging Station SHALL respond with a GetInstalledCertificateIdsResponse.
    Precondition: After receiving a GetInstalledCertificateIdsRequest
System under test: CSMS

Description:
    The CSMS is able to retrieve the certificates installed at the Charging Station using the
    GetInstalledCertificateIdsRequest message. It supports all available hash algorithms, including
    SHA256, SHA384, and SHA512.

Purpose:
    To verify if the CSMS is able to retrieve the hashData from all CSMSRootCertificates stored at
    the Charging Station, using all available hash algorithms, including SHA256, SHA384, and SHA512.

Main:
    1. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate.
       The OCTT responds with data hashed with SHA256.
    2. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate.
       The OCTT responds with data hashed with SHA384.
    3. Execute Reusable State GetInstalledCertificates for certificateType CSMSRootCertificate.
       The OCTT responds with data hashed with SHA512.

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


def make_certificate_hash_data_chain(cert_type, hash_algorithm):
    """Create a CertificateHashDataChain response for the given type and hash algorithm."""
    return [{
        'certificate_type': cert_type,
        'certificate_hash_data': {
            'hash_algorithm': hash_algorithm,
            'issuer_name_hash': 'aabbccdd' * 8,
            'issuer_key_hash': 'eeff0011' * 8,
            'serial_number': '01020304',
        },
    }]


@pytest.mark.asyncio
async def test_tc_m_12():
    """Retrieve certificates from Charging Station - CSMSRootCertificate."""
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

    hash_algorithms = [
        HashAlgorithmEnumType.sha256,
        HashAlgorithmEnumType.sha384,
        HashAlgorithmEnumType.sha512,
    ]

    # Configure initial response with SHA256
    cp._get_installed_certificate_ids_response_status = GetInstalledCertificateStatusEnumType.accepted
    cp._get_installed_certificate_ids_response_chain = make_certificate_hash_data_chain(
        GetCertificateIdUseEnumType.csms_root_certificate,
        hash_algorithms[0],
    )

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    for i, hash_algo in enumerate(hash_algorithms):
        # Update response chain with current hash algorithm
        cp._get_installed_certificate_ids_response_chain = make_certificate_hash_data_chain(
            GetCertificateIdUseEnumType.csms_root_certificate,
            hash_algo,
        )

        # Wait for CSMS to send GetInstalledCertificateIdsRequest
        await asyncio.wait_for(
            cp._received_get_installed_certificate_ids.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )

        # Validate request content
        assert cp._get_installed_certificate_ids_data is not None
        cert_type = cp._get_installed_certificate_ids_data['certificate_type']
        assert cert_type is not None, "certificateType must be present"

        # Tool validation: certificateType must contain CSMSRootCertificate
        if isinstance(cert_type, list):
            assert GetCertificateIdUseEnumType.csms_root_certificate in cert_type, \
                f"Expected CSMSRootCertificate in certificateType list, got {cert_type}"
        else:
            assert cert_type == GetCertificateIdUseEnumType.csms_root_certificate, \
                f"Expected CSMSRootCertificate, got {cert_type}"

        logging.info(f"TC_M_12 step {i + 1} ({hash_algo}) completed successfully")

        # Reset event for next iteration
        cp._received_get_installed_certificate_ids.clear()

    logging.info("TC_M_12 completed successfully")
    start_task.cancel()
    await ws.close()
