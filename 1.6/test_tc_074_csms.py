"""
Test case name      Update Charge Point Certificate by request of Central System
Test case Id        TC_074_CSMS
Document ref        Table 185, page 159/176 (CompliancyTestTool-TestCaseDocument, 2025-11)
Section             3.21.1 Secure connection setup
System under test   Central System

Description         When SUT Charge Point, the tool shall take on the role of both Central System and Certificate Authority
                    Server. Which means it will sign the certificate with its own certificate.
                    NOTE: The description above is verbatim from the PDF. It references "SUT Charge Point" but
                    this is a CSMS test (SUT = Central System). Possible doc error — to be verified.

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
from trigger import trigger_v16
from utils import (
    create_ssl_context, generate_csr,
    save_cert_chain_to_temp, save_private_key_to_temp,
)

SP3_CP = os.environ['CP16_SP3']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CSMS_ADDRESS = os.environ['CSMS_ADDRESS']


@pytest.mark.asyncio
async def test_tc_074():
    # Profile 3 (mTLS): connect with client certificate, no BasicAuth
    ssl_ctx = create_ssl_context(
        ca_cert=os.environ.get('TLS_CA_CERT'),
        client_cert=os.environ.get('TLS_CLIENT_CERT'),
        client_key=os.environ.get('TLS_CLIENT_KEY'),
        check_hostname=False,
    )
    ws = await websockets.connect(
        uri=f'{CSMS_ADDRESS}/{SP3_CP}',
        subprotocols=['ocpp1.6'],
        ssl=ssl_ctx,
    )
    assert ws.open
    cp = TziChargePoint16(SP3_CP, ws)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ExtendedTriggerMessage.req
    asyncio.create_task(trigger_v16(SP3_CP, 'extended-trigger-message', {
        'requestedMessage': 'SignChargePointCertificate',
    }))
    await asyncio.wait_for(cp._received_extended_trigger.wait(), timeout=ACTION_TIMEOUT)
    assert cp._extended_trigger_requested == 'SignChargePointCertificate'

    # Step 3-4: CP generates a CSR and sends SignCertificate.req
    csr_pem, private_key = generate_csr(SP3_CP)
    sign_response = await cp.send_sign_certificate(csr=csr_pem)
    assert sign_response.status == GenericStatus.accepted

    # Generate a self-signed cert from the CSR for testing
    from cryptography.x509 import load_pem_x509_csr, CertificateBuilder, random_serial_number
    from cryptography.hazmat.primitives import hashes, serialization
    import datetime as dt

    csr_obj = load_pem_x509_csr(csr_pem.encode())
    cert = (
        CertificateBuilder()
        .subject_name(csr_obj.subject)
        .issuer_name(csr_obj.subject)
        .public_key(csr_obj.public_key())
        .serial_number(random_serial_number())
        .not_valid_before(dt.datetime.now(dt.timezone.utc))
        .not_valid_after(dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )
    cert_chain_pem = cert.public_bytes(serialization.Encoding.PEM).decode()

    # Step 5-6: Wait for CSMS to send CertificateSigned.req
    asyncio.create_task(trigger_v16(SP3_CP, 'certificate-signed', {
        'certificateChain': cert_chain_pem,
    }))
    await asyncio.wait_for(cp._received_certificate_signed.wait(), timeout=ACTION_TIMEOUT)
    cert_chain = cp._certificate_signed_chain
    assert cert_chain is not None

    start_task.cancel()
    await ws.close()

    # Step 7-8: CP reconnects with the new certificate
    cert_path = save_cert_chain_to_temp(cert_chain)
    key_path = save_private_key_to_temp(private_key)
    try:
        ssl_ctx_new = create_ssl_context(
            ca_cert=os.environ.get('TLS_CA_CERT'),
            client_cert=cert_path,
            client_key=key_path,
            check_hostname=False,
        )
        ws2 = await websockets.connect(
            uri=f'{CSMS_ADDRESS}/{SP3_CP}',
            subprotocols=['ocpp1.6'],
            ssl=ssl_ctx_new,
        )
        assert ws2.open
        await ws2.close()
    finally:
        os.unlink(cert_path)
        os.unlink(key_path)
