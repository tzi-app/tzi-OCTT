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

Test System:
    The configured (V2G) certificate chain is in certs/ (contract_pki.py): V2G root CA -> sub-CA.
    The ocspRequestData holds the hashes of the sub-CA, with the responder URL of the Test System's
    OCSP service, mock_ocsp_responder.py. The mock answers about the requested certificate, signed by
    the root CA. The CSMS passes the answer on to the Charging Station, which verifies it.

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
"""
import asyncio
import base64
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
)
from cryptography.x509 import ocsp

import contract_pki
from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, build_default_ssl_context
from mock_ocsp_responder import MockOCSPResponder

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])

OCSP_PORT = 19080


@pytest.mark.asyncio
async def test_tc_m_24():
    """Get Charging Station Certificate status - Success."""
    ocsp_responder = MockOCSPResponder(port=OCSP_PORT, cert_status="good")
    ocsp_responder.start()

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

        # Step 1: CS sends GetCertificateStatusRequest with the OCSP data of the configured chain's sub-CA
        ocsp_request_data = contract_pki.ocsp_request_data(
            contract_pki.load_certificate(contract_pki.SUB_CA),
            contract_pki.load_certificate(contract_pki.ROOT_CA),
            f'http://localhost:{OCSP_PORT}',
        )

        response = await cp.send_get_certificate_status_request(ocsp_request_data)

        # Tool validation Step 2: status must be Accepted
        assert response.status == GetCertificateStatusEnumType.accepted, \
            f"Expected GetCertificateStatusResponse status=Accepted, got {response.status}"

        # Tool validation Step 2: ocspResult must be present
        assert response.ocsp_result is not None and len(response.ocsp_result) > 0, \
            "ocspResult must be present in GetCertificateStatusResponse"
        # Tool validation Step 2: ocspResult is an OCSPResponse (RFC 6960), DER encoded, then base64 encoded
        try:
            ocsp_response = ocsp.load_der_ocsp_response(base64.b64decode(response.ocsp_result, validate=True))
        except ValueError as exc:
            pytest.fail(f"ocspResult is not a base64 encoded DER OCSPResponse: {exc}")
        logging.info(f"ocspResult: OCSPResponse with responseStatus {ocsp_response.response_status.name}")

        logging.info("TC_M_24 completed successfully")
        start_task.cancel()
        await ws.close()
    finally:
        ocsp_responder.stop()
