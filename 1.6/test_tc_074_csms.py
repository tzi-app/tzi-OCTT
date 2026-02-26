"""
Test case name      Update Charge Point Certificate by request of Central System
Test case Id        TC_074_CSMS
Document ref        Table 185, page 159/176 (CompliancyTestTool-TestCaseDocument, 2025-11)
Section             3.21.1 Secure connection setup
System under test   Central System

Description         When SUT Charge Point, the tool shall take on the role of both Central System and Certificate Authority
                    Server. Which means it will sign the certificate with its own certificate.

Purpose             To check if the Central System is able to request the Charge Point to renew its ChargePointCertificate.

Prerequisite(s)     The Central System supports security profile 3.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1. The Central System sends an ExtendedTriggerMessage.req
    2. The Charge Point responds with an ExtendedTriggerMessage.conf

    [The Charge Point generates a new public/private key pair and generates a Certificate Signing Request.]
    3. The Charge Point sends a SignCertificate.req

    4. The Central System responds with a SignCertificate.conf
    [Certificate Authority Server signs the certificate.]
    5. The Central System sends a CertificateSigned.req

    [The Charge Point verifies the validity of the signed certificate.]
    6. The Charge Point responds with a CertificateSigned.conf

    7. The Charge Point disconnects its current connection and reconnects to the Central System
       with the new certificate.
    8. The Central System accepts the incoming connection request using the new certificate.

Tool Validations
    * Step 1:
        (Message: ExtendedTriggerMessage.req)
        The requestedMessage is SignChargePointCertificate
        The connectorId is <Omitted>

    * Step 2:
        (Message: ExtendedTriggerMessage.conf)
        The status is Accepted

    * Step 4:
        (Message: SignCertificate.conf)
        The status is Accepted

    * Step 5:
        (Message: CertificateSigned.req)
        The certificateChain:
        * The certificateChain field contains valid PEM encoding.
        * The Public key of the client certificate matches the public key generated for the CSR at step 3.
        * The client certificate is signed using the configured security algorithm type.
        * The subject field commonName equals the configured serialNumber.
        * The public key of the client certificate adheres to the minimal OCPP key length
          requirements (RSA: 2048 / ECDSA: 224).

    * Step 6:
        (Message: CertificateSigned.conf)
        The status is Accepted

    * Step 7:
        The Charge Point reconnects to the Central System with the new certificate.

Expected result(s) / behaviour:
    The Charge Point and the Central System are connected.
"""

import asyncio
import os
import pytest
import websockets

from ocpp.v16.enums import GenericStatus

from charge_point import TziChargePoint16
from utils import (
    create_ssl_context, generate_csr, get_basic_auth_headers,
    save_cert_chain_to_temp, save_private_key_to_temp,
)

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CSMS_WSS_ADDRESS = os.environ.get('CSMS_WSS_ADDRESS', 'wss://localhost:8082')


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_074(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ExtendedTriggerMessage.req
    await asyncio.wait_for(cp._received_extended_trigger.wait(), timeout=ACTION_TIMEOUT)
    assert cp._extended_trigger_requested == 'SignChargePointCertificate'

    # Step 3-4: CP generates a CSR and sends SignCertificate.req
    csr_pem, private_key = generate_csr(BASIC_AUTH_CP)
    sign_response = await cp.send_sign_certificate(csr=csr_pem)
    assert sign_response.status == GenericStatus.accepted

    # Step 5-6: Wait for CSMS to send CertificateSigned.req
    await asyncio.wait_for(cp._received_certificate_signed.wait(), timeout=ACTION_TIMEOUT)
    cert_chain = cp._certificate_signed_chain
    assert cert_chain is not None

    start_task.cancel()
    await connection.close()

    # Step 7-8: CP reconnects with the new certificate
    cert_path = save_cert_chain_to_temp(cert_chain)
    key_path = save_private_key_to_temp(private_key)
    try:
        ssl_ctx = create_ssl_context(
            ca_cert=os.environ.get('TLS_CA_CERT'),
            client_cert=cert_path,
            client_key=key_path,
            check_hostname=False,
        )
        ws = await websockets.connect(
            uri=f'{CSMS_WSS_ADDRESS}/{BASIC_AUTH_CP}',
            subprotocols=['ocpp1.6'],
            ssl=ssl_ctx,
        )
        assert ws.open
        await ws.close()
    finally:
        os.unlink(cert_path)
        os.unlink(key_path)
