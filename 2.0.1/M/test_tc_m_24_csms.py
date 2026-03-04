"""
TC_M_24 - Get Charging Station Certificate status - Success
Use case: M06 | Requirements: M06.FR.01, M06.FR.02, M06.FR.03, M06.FR.08, M06.FR.09
M06.FR.01: After receiving a GetCertificateStatusRequest The CSMS SHALL respond with a GetCertificateStatusResponse.
    Precondition: After receiving a GetCertificateStatusRequest
M06.FR.02: The CSMS SHALL include the OCSP response data in the OCSPResult field in the GetCertificateStatusResponse.
    Precondition: M06.FR.01 AND The CSMS was successful in retrieving the OCSP certificate status
M06.FR.03: When receiving GetInstalledCertificateIdsRequest, the Charging Station SHALL respond with GetInstalledCertificateIdsResponse containing certificate information.
    Precondition: M06.FR.02
M06.FR.08: The CSMS SHALL format the response data according to OCSPResponse as defined in IETF RFC 6960, formatted according to ASN.1 [X.680].
M06.FR.09: The OCSPResponse data SHALL be DER encoded.
System under test: CSMS

Description:
    The Charging Station is able to request the CSMS to get the status of a (V2G) Charging Station
    certificate.

Purpose:
    To verify if the CSMS is able to provide the status of a requested (V2G) Charging Station certificate.

Main:
    1. The OCTT sends one or more subsequent GetCertificateStatusRequests
       with ocspRequestData contains hashes from configured (V2G) certificate chain SubCA's.
    2. The CSMS responds with a GetCertificateStatusResponse

Tool validations:
    * Step 2: GetCertificateStatusResponse
      - status = Accepted
      - ocspResult = <OCSPResponse class as defined in IETF RFC 6960, DER encoded, base64 encoded>

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
    GetCertificateStatusEnumType,
    HashAlgorithmEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
async def test_tc_m_24():
    """Get Charging Station Certificate status - Success."""
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
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1: CS sends GetCertificateStatusRequest with OCSP data
    ocsp_request_data = {
        'hash_algorithm': HashAlgorithmEnumType.sha256,
        'issuer_name_hash': 'aabbccdd' * 8,
        'issuer_key_hash': 'eeff0011' * 8,
        'serial_number': '01020304',
        'responder_url': 'http://ocsp.example.com',
    }

    response = await cp.send_get_certificate_status_request(ocsp_request_data)

    # Tool validation Step 2: status must be Accepted
    assert response.status == GetCertificateStatusEnumType.accepted, \
        f"Expected GetCertificateStatusResponse status=Accepted, got {response.status}"

    # Tool validation Step 2: ocspResult must be present
    assert response.ocsp_result is not None and len(response.ocsp_result) > 0, \
        "ocspResult must be present in GetCertificateStatusResponse"

    logging.info("TC_M_24 completed successfully")
    start_task.cancel()
    await ws.close()
