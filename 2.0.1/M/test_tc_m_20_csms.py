"""
TC_M_20 - Delete a certificate from a Charging Station - Success
Use case: M04 | Requirements: M04.FR.01, M04.FR.07
M04.FR.01: After receiving a DeleteCertificateRequest The Charging Station SHALL respond with a DeleteCertificateResponse.
    Precondition: After receiving a DeleteCertificateRequest
M04.FR.07: When deleting a certificate The CSMS SHALL use the same hashAlgorithm as the Charging Station uses to report the certificateHashData for the certificate in the GetInstalledCertificateIdsResponse. This ensures CSMS uses a hashAlgorithm that is supported by the Charging Station.
    Precondition: When deleting a certificate
System under test: CSMS

Description:
    The CSMS is able to request the Charging Station to delete an installed certificate using the
    DeleteCertificateRequest message, using all available hash algorithms, including SHA256, SHA384,
    and SHA512.

Purpose:
    To verify if CSMS is able to request a Charging Station to delete an installed certificate,
    using all available hash algorithms, including SHA256, SHA384, and SHA512.

Main (repeated for each hash algorithm SHA256, SHA384, SHA512):
    1. CertificateInstalled with certificateType CSMSRootCertificate.
    Manual Action: Request the CSMS to send a DeleteCertificateRequest.
    2. The CSMS sends a GetInstalledCertificateIdsRequest
    3. The OCTT responds with a GetInstalledCertificateIdsResponse
       with status = Accepted
       certificateHashDataChain contains an entry with:
         certificateHashDataChain[0].certificateType = CSMSRootCertificate
         certificateHashDataChain[0].certificateHashData.hashAlgorithm = <current hash>
    4. The CSMS sends a DeleteCertificateRequest
    5. The OCTT responds with a DeleteCertificateResponse with status = Accepted

Tool validations:
    * Step 2: GetInstalledCertificateIdsRequest
      - certificateType contains CSMSRootCertificate OR is omitted.
    * Step 4: DeleteCertificateRequest
      - certificateHashData is the returned certificateHashData at Step 3.

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
    InstallCertificateStatusEnumType,
    GetCertificateIdUseEnumType,
    GetInstalledCertificateStatusEnumType,
    DeleteCertificateStatusEnumType,
    HashAlgorithmEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_m_20():
    """Delete a certificate from a Charging Station - Success."""
    hash_algorithms = [
        HashAlgorithmEnumType.sha256,
        HashAlgorithmEnumType.sha384,
        HashAlgorithmEnumType.sha512,
    ]

    for hash_algo in hash_algorithms:
        logging.info(f"TC_M_20 - Testing with hash algorithm: {hash_algo}")

        cp_id = BASIC_AUTH_CP
        uri = f'{CSMS_ADDRESS}/{cp_id}'
        headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

        ws = await websockets.connect(
            uri=uri,
            subprotocols=['ocpp2.0.1'],
            extra_headers=headers,
        )
        time.sleep(0.5)

        hash_data = {
            'hash_algorithm': hash_algo,
            'issuer_name_hash': 'aabbccdd' * 8,
            'issuer_key_hash': 'eeff0011' * 8,
            'serial_number': '01020304',
        }

        cp = TziChargePoint(cp_id, ws)
        # Configure responses
        cp._install_certificate_response_status = InstallCertificateStatusEnumType.accepted
        cp._get_installed_certificate_ids_response_status = GetInstalledCertificateStatusEnumType.accepted
        cp._get_installed_certificate_ids_response_chain = [{
            'certificate_type': GetCertificateIdUseEnumType.csms_root_certificate,
            'certificate_hash_data': hash_data,
        }]
        cp._delete_certificate_response_status = DeleteCertificateStatusEnumType.accepted

        start_task = asyncio.create_task(cp.start())

        # Boot and establish session
        boot_response = await cp.send_boot_notification()
        assert boot_response.status == RegistrationStatusEnumType.accepted

        await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

        # Step 1: Reusable State CertificateInstalled - Wait for InstallCertificateRequest
        await asyncio.wait_for(
            cp._received_install_certificate.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )
        assert cp._install_certificate_data is not None

        # Step 2: Wait for CSMS to send GetInstalledCertificateIdsRequest
        await asyncio.wait_for(
            cp._received_get_installed_certificate_ids.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )
        assert cp._get_installed_certificate_ids_data is not None

        # Tool validation Step 2: certificateType contains CSMSRootCertificate OR is omitted
        cert_type = cp._get_installed_certificate_ids_data['certificate_type']
        if cert_type is not None:
            if isinstance(cert_type, list):
                assert GetCertificateIdUseEnumType.csms_root_certificate in cert_type, \
                    f"Expected CSMSRootCertificate in list, got {cert_type}"
            else:
                assert cert_type == GetCertificateIdUseEnumType.csms_root_certificate, \
                    f"Expected CSMSRootCertificate, got {cert_type}"

        # Step 4: Wait for CSMS to send DeleteCertificateRequest
        await asyncio.wait_for(
            cp._received_delete_certificate.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )
        assert cp._delete_certificate_data is not None

        # Tool validation Step 4: certificateHashData matches returned data from Step 3 (M04.FR.07)
        delete_hash = cp._delete_certificate_data['certificate_hash_data']
        assert delete_hash is not None, "certificateHashData must be present in DeleteCertificateRequest"

        # CSMS SHALL use the same hashAlgorithm as reported in GetInstalledCertificateIdsResponse
        assert delete_hash['hash_algorithm'] == hash_data['hash_algorithm'], \
            f"Expected hash_algorithm={hash_data['hash_algorithm']}, got {delete_hash['hash_algorithm']}"
        assert delete_hash['issuer_name_hash'] == hash_data['issuer_name_hash'], \
            f"Expected issuer_name_hash={hash_data['issuer_name_hash']}, got {delete_hash['issuer_name_hash']}"
        assert delete_hash['issuer_key_hash'] == hash_data['issuer_key_hash'], \
            f"Expected issuer_key_hash={hash_data['issuer_key_hash']}, got {delete_hash['issuer_key_hash']}"
        assert delete_hash['serial_number'] == hash_data['serial_number'], \
            f"Expected serial_number={hash_data['serial_number']}, got {delete_hash['serial_number']}"

        logging.info(f"TC_M_20 ({hash_algo}) completed successfully")
        start_task.cancel()
        await ws.close()

    logging.info("TC_M_20 completed successfully for all hash algorithms")
