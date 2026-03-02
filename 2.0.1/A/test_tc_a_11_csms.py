"""
Test case name      Update Charging Station Certificate by request of CSMS - Success - Charging Station Certificate
Test case Id        TC_A_11_CSMS
Use case Id(s)      A02 & F06
Requirement(s)      A02.FR.11, A02.FR.14 & F06.FR.01

Requirement Details:
    A02.FR.11: Upon receipt of a SignCertificateRequest AND It is able to process the request The CSMS SHALL set status to Accepted in the SignCertificateResponse.
        Precondition: Upon receipt of a SignCertificateRequest AND It is able to process the request
    A02.FR.14: When receiving a SignCertificateRequest with certificateType included It is RECOMMENDED for the CSMS to set the certificateType field in the CertificateSignedRequest to the type of certificate in the SignCertificateRequest.
        Precondition: When receiving a SignCertificateRequest with certificateType included
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to receive.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to update its charging station certificate using the
                    TriggerMessageRequest message.

Purpose             To verify if the CSMS is able to request the Charging Station to update its Charging Station
                    Certificate.

Prerequisite(s)     The CSMS supports security profile 3

Test Scenario
1. Execute Reusable State RenewChargingStationCertificate
2. The OCTT disconnects its current connection and reconnects to the CSMS with the new certificate.
3. The CSMS accepts the incoming connection request using the new certificate.

Tool validations
    N/a

Post scenario validations:
    The OCTT and the CSMS are connected.
"""

import asyncio
import os
import time
import logging

import pytest
import websockets

from ocpp.v201.enums import (
    GenericStatusEnumType, CertificateSignedStatusEnumType,
    CertificateSigningUseEnumType
)

from tzi_charge_point import TziChargePoint
from utils import create_ssl_context, generate_csr, save_private_key_to_temp, save_cert_chain_to_temp

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
TLS_CA_CERT = os.environ['TLS_CA_CERT']
TLS_CLIENT_CERT = os.environ['TLS_CLIENT_CERT']
TLS_CLIENT_KEY = os.environ['TLS_CLIENT_KEY']
SECURITY_PROFILE_3_CP = os.environ['SECURITY_PROFILE_3_CP_A']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_a_11():
    cp_id = SECURITY_PROFILE_3_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    ssl_ctx = create_ssl_context(
        ca_cert=TLS_CA_CERT,
        client_cert=TLS_CLIENT_CERT,
        client_key=TLS_CLIENT_KEY,
    )
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        ssl=ssl_ctx,
    )

    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    cp._certificate_signed_response_status = CertificateSignedStatusEnumType.accepted
    start_task = asyncio.create_task(cp.start())

    # Step 1: Execute Reusable State RenewChargingStationCertificate
    # Wait for CSMS to send TriggerMessageRequest(SignChargingStationCertificate)
    await asyncio.wait_for(
        cp._received_trigger_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._trigger_message_data == 'SignChargingStationCertificate', \
        f"Expected SignChargingStationCertificate, got: {cp._trigger_message_data}"

    # Generate a real CSR with a real key pair
    csr_pem, private_key = generate_csr(cp_id)

    # Send SignCertificateRequest with the real CSR
    sign_response = await cp.send_sign_certificate_request(
        csr=csr_pem,
        certificate_type=CertificateSigningUseEnumType.charging_station_certificate,
    )
    assert sign_response.status == GenericStatusEnumType.accepted, \
        f"Expected SignCertificateResponse Accepted, got: {sign_response.status}"

    # Wait for CSMS to send CertificateSignedRequest
    await asyncio.wait_for(
        cp._received_certificate_signed.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._certificate_signed_data is not None
    assert cp._certificate_signed_data['certificate_chain'], \
        "CertificateSignedRequest must contain a certificate chain"
    cert_type = cp._certificate_signed_data.get('certificate_type')
    assert cert_type in (
        CertificateSigningUseEnumType.charging_station_certificate,
        'ChargingStationCertificate',
    ), f"Expected certificateType ChargingStationCertificate, got: {cert_type}"

    new_cert_chain = cp._certificate_signed_data['certificate_chain']
    logging.info(f"Received signed certificate chain (length={len(new_cert_chain)})")

    start_task.cancel()
    await ws.close()

    # Step 2-3: Reconnect using the NEW certificate from the renewal process.
    new_cert_path = save_cert_chain_to_temp(new_cert_chain)
    new_key_path = save_private_key_to_temp(private_key)
    try:
        new_ssl_ctx = create_ssl_context(
            ca_cert=TLS_CA_CERT,
            client_cert=new_cert_path,
            client_key=new_key_path,
        )
        ws_reconnect = await websockets.connect(
            uri=uri,
            subprotocols=['ocpp2.0.1'],
            ssl=new_ssl_ctx,
        )
        assert ws_reconnect.open, "CSMS must accept connection after charging station certificate renewal"
        await ws_reconnect.close()
    finally:
        os.unlink(new_cert_path)
        os.unlink(new_key_path)
