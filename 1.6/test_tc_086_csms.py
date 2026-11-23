"""
Test case name      TLS - server-side certificate - Valid certificate
Test case Id        TC_086_CSMS
Section             3.21 Security (appears after 3.21.3 in the document, no numbered subsection heading;
                    topic heading is "TLS - server-side certificate - Valid certificate")
System under test   Central System
Document ref        Table 196, doc pages 170-171 (CompliancyTestTool-TestCaseDocument-CSMS-Section3, 2025-11)

Description         The Central System uses a server-side certificate to identify itself to the Charge Point, when using security
                    profile 2 or 3.

Purpose             To verify whether the Central System is able to provide a valid server certificate and setup a secured
                    WebSocket connection.

Prerequisite(s)     The Central System supports security profile 2 and/or 3.

Before (Preparations)
    Configuration State: N/A
    Memory State: N/A
    Reusable State(s): The OCTT closes the connection.

Test Scenario
    1. The Charge Point initiates a TLS handshake and sends a Client Hello to the Central System.
    2. The Central System responds with a Server Hello With the <Configured server certificate>

    3. The Charge Point performs the following actions:
        Send client certificate
        Client Key Exchange
        Certificate verify
        Change Cipher Spec
        Finished

        Note(s):
        - The client certificate is only sent when the Central System uses security profile 3.

    4. The Central System performs the following actions:
        Change Cipher Spec
        Finished

    5. The Charge Point sends a HTTP upgrade request to the Central System

        Note(s):
        - The HTTP request only contains a username/password combination when the Central System uses
          security profile 2.

    6. The Central System upgrades the connection to a (secured) WebSocket connection.

    7. The Charge Point sends a BootNotification.req
    8. The Central System responds with a BootNotification.conf

    [Send per connector and connectorId=0.]
    9. The Charge Point sends a StatusNotification.req
    10. The Central System responds with a StatusNotification.conf

Tool Validations
    * Step 2:
        The OCTT validates the following before finishing the TLS handshake:
        - The Central System must use TLS version 1.2 or above
        At least the following set of cipher suites must be supported:
            TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
            AND TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
            AND TLS_RSA_WITH_AES_128_GCM_SHA256
            AND TLS_RSA_WITH_AES_256_GCM_SHA384
        - When using RSA or DSA the key must be at least 2048 bits long.
          and when using elliptic curve cryptography the key must be at least 224 bits long.
        - The received server side certificate must be transmitted in the X.509 format encoded in
          Privacy-Enhanced Mail (PEM) format.
        - The certificate must include a serial number.
        - The subject field of the certificate must contain a commonName RDN which consists of the FQDN of
          the endpoint of the server.
        NOTE: If one of the above validations fails, the OCTT can still proceed with the next steps of the
        testcase (if it is able to), but the testcase will FAIL and the OCTT reports why it failed.

    Post scenario validations: N/A

Expected result(s) / behaviour: N/A (no explicit expected result row in document)

Implementation Notes:
    - The expected BootNotification.conf status is not specified in the test case document. Test assumes Accepted.
    - Covers security profile 2: TLS with the server certificate, with the username/password in the HTTP request.
      TC_087 covers security profile 3 (client certificates).
    - The Charge Point is CP16_SP1. Every connection of this suite runs over TLS, so its connection is the one
      described for security profile 2. CP16_SP2 is not used: TC_083 upgrades it to security profile 3, and the
      1.6 tests run in one pytest session.
    - Cipher suites: a handshake negotiates one suite, so each required TLS 1.2 suite gets a TLS handshake of its
      own that offers only that suite. Each one is steps 1-4 with the step 2 validations, and the connection is
      terminated before any HTTP upgrade. These handshakes run before the connection that goes through steps 1-10.
    - The step 2 certificate validations run on every certificate the Central System serves: the one of the
      connection of steps 1-10, and the one of each cipher suite handshake. The ECDHE_ECDSA suites are served an EC
      certificate, and the TLS_RSA suites an RSA certificate.
    - The commonName is compared with the host of CSMS_ADDRESS, the endpoint of the server.

Ambiguities in the test case document:
    - Step 9: "[Send per connector and connectorId=0.]" — unclear whether this means "for each connector
      including connectorId=0" or "for each connector starting at connectorId=0". Implementation sends
      StatusNotification for connectorId=0 (charge point) and connectorId=1 (single physical connector).
      The number of physical connectors is not specified in the test case.
"""

import asyncio
import contextlib
import os
import ssl
from urllib.parse import urlparse

import pytest
import websockets
from cryptography.x509 import load_der_x509_certificate
from cryptography.x509.oid import NameOID

from ocpp.v16.enums import RegistrationStatus

from charge_point import TziChargePoint16
from utils import (create_ssl_context, get_basic_auth_headers, get_tls_info,
                    validate_cert_key_size, validate_cert_x509_pem)

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ADDRESS = os.environ['CSMS_ADDRESS']

# Step 2: the required TLS 1.2 cipher suites, by their OpenSSL names
REQUIRED_TLS12_CIPHERS = (
    'ECDHE-ECDSA-AES128-GCM-SHA256',  # TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    'ECDHE-ECDSA-AES256-GCM-SHA384',  # TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    'AES128-GCM-SHA256',              # TLS_RSA_WITH_AES_128_GCM_SHA256
    'AES256-GCM-SHA384',              # TLS_RSA_WITH_AES_256_GCM_SHA384
)


def validate_server_certificate(der_cert, server_host):
    """Step 2 validations on a certificate the Central System served: the key size, the X.509 PEM format,
    a serial number, and a commonName RDN that consists of the FQDN of the endpoint."""
    # Key size: RSA/DSA >= 2048 bits, ECC >= 224 bits
    validate_cert_key_size(der_cert)
    validate_cert_x509_pem(der_cert)

    cert = load_der_x509_certificate(der_cert)
    assert cert.serial_number is not None and cert.serial_number > 0, \
        "Certificate must include a serial number"
    common_names = [attribute.value for attribute in cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)]
    assert common_names, "Certificate subject must contain a commonName RDN"
    assert server_host in common_names, \
        f"The commonName must consist of the FQDN of the endpoint ({server_host}), got {common_names}"


async def assert_tls12_cipher_suites_supported(uri):
    """Step 2: the Central System supports each required cipher suite, checked with a TLS 1.2 handshake per
    suite that offers only that suite. Each handshake is closed without an HTTP upgrade. That makes it a check
    of the TLS layer, and the Central System does not see it as a connection of the Charge Point."""
    endpoint = urlparse(uri)
    host, port = endpoint.hostname, endpoint.port or 443
    for cipher in REQUIRED_TLS12_CIPHERS:
        ssl_ctx = create_ssl_context(ca_cert=os.environ.get('TLS_CA_CERT'), check_hostname=False)
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.set_ciphers(cipher)

        try:
            _, writer = await asyncio.open_connection(host, port, ssl=ssl_ctx, server_hostname=host)
        except Exception as exc:
            pytest.fail(f"Required TLS 1.2 cipher suite not supported: {cipher}, error={exc}")

        try:
            ssl_obj = writer.get_extra_info('ssl_object')
            negotiated = ssl_obj.cipher()[0]
            assert negotiated == cipher, f"Expected cipher suite {cipher}, negotiated {negotiated}"
            validate_server_certificate(ssl_obj.getpeercert(binary_form=True), host)
        finally:
            writer.close()
            with contextlib.suppress(ConnectionError, ssl.SSLError):
                await writer.wait_closed()


@pytest.mark.asyncio
async def test_tc_086():
    uri = f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}'
    server_host = urlparse(uri).hostname

    # Step 2 validation, cipher suites. A handshake negotiates one suite, so each required suite gets a TLS
    # handshake of its own (steps 1-4), terminated before any HTTP upgrade. These run before the connection
    # that goes through steps 1-10.
    await assert_tls12_cipher_suites_supported(uri)

    # Step 1-6 (security profile 2): TLS handshake with the server certificate only, then the WebSocket
    # upgrade with the username/password
    ssl_ctx = create_ssl_context(
        ca_cert=os.environ.get('TLS_CA_CERT'),
        check_hostname=False,
    )
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp1.6'],
        ssl=ssl_ctx,
        extra_headers=get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD),
    )
    assert ws.open

    # Tool Validation (Step 2) on this connection: TLS version and the server certificate
    tls_info = get_tls_info(ws)
    assert tls_info is not None
    assert tls_info['tls_version'] in ('TLSv1.2', 'TLSv1.3'), \
        f"Expected TLS 1.2+, got {tls_info['tls_version']}"
    validate_server_certificate(tls_info['peer_cert_der'], server_host)

    cp = TziChargePoint16(BASIC_AUTH_CP, ws)
    start_task = asyncio.create_task(cp.start())

    # Step 7-8: BootNotification
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 9-10: StatusNotification per connector
    for cid in (0, 1):
        await cp.send_status_notification(cid)

    start_task.cancel()
    await ws.close()
