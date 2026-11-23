"""
Test case name      TLS - Client-side certificate - valid certificate
Test case Id        TC_087_CSMS
Section             3.21 Security
System under test   Central System
Document ref        CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, Table 197, pages 171-172

Description         The Charge Point uses a client-side certificate to identify itself to the Central System, when using security
                    profile 3.

Purpose             To verify whether the Central System is able to receive a client certificate provided by a Charge Point and
                    setup a secured WebSocket connection.

Prerequisite(s)     The Central System supports security profile 3.

Before (Preparations)
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): N/a

Test Scenario
    1. The Charge Point initiates a TLS handshake and sends a Client Hello to the Central System.
    2. The Central System responds with a Server Hello with the <Configured server certificate>

    3. The Charge Point performs the following actions:
        Send client certificate
        Client Key Exchange
        Certificate verify
        Change Cipher Spec
        Finished

    4. The Central System performs the following actions:
        Change Cipher Spec
        Finished

    5. The Charge Point sends a HTTP upgrade request to the Central System
    6. The Central System upgrades the connection to a (secured) WebSocket connection.

    7. The Charge Point sends a BootNotification.req
    8. The Central System responds with a BootNotification.conf

    [Send per connector and connectorId=0.]
    9. The Charge Point sends a StatusNotification.req
    10. The Central System responds with a StatusNotification.conf

Tool Validations
    * Step 3:
        The OCTT validates the following before finishing the TLS handshake:
        - The Central System must use TLS version 1.2 or above
        At least the following set of cipher suites must be supported:
            TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
            AND TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
            AND TLS_RSA_WITH_AES_128_GCM_SHA256
            AND TLS_RSA_WITH_AES_256_GCM_SHA384

    Post scenario validations: N/a

Expected result(s) / behaviour: N/a

Implementation notes:
    - Cipher suites: a handshake negotiates one suite, so each required TLS 1.2 suite gets a TLS handshake of its
      own that offers only that suite and sends the client certificate. Each one is steps 1-4 with the step 3
      validations, and the connection is terminated before any HTTP upgrade. These handshakes run before the
      connection that goes through steps 1-10.
    - Step 9 "[Send per connector and connectorId=0]": Ambiguous on how many connectors.
      Implemented as connectorId=0 (CP itself) + connectorId=1 (assumes 1 physical connector).
    - The docstring does not specify the expected BootNotification.conf status; test asserts 'Accepted'
      which is consistent with a successful connection scenario.
"""

import asyncio
import contextlib
import os
import ssl
from urllib.parse import urlparse

import pytest
import websockets

from ocpp.v16.enums import RegistrationStatus

from charge_point import TziChargePoint16
from utils import create_ssl_context

SP3_CP = os.environ['CP16_SP3']
CSMS_ADDRESS = os.environ['CSMS_ADDRESS']

# Step 3: the required TLS 1.2 cipher suites, by their OpenSSL names
REQUIRED_TLS12_CIPHERS = (
    'ECDHE-ECDSA-AES128-GCM-SHA256',  # TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    'ECDHE-ECDSA-AES256-GCM-SHA384',  # TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    'AES128-GCM-SHA256',              # TLS_RSA_WITH_AES_128_GCM_SHA256
    'AES256-GCM-SHA384',              # TLS_RSA_WITH_AES_256_GCM_SHA384
)


async def assert_tls12_cipher_suites_supported(uri):
    """Step 3: the Central System supports each required cipher suite, checked with a TLS 1.2 handshake per
    suite that offers only that suite and sends the client certificate. Each handshake is closed without an
    HTTP upgrade. That makes it a check of the TLS layer, and the Central System does not see it as a
    connection of the Charge Point."""
    endpoint = urlparse(uri)
    host, port = endpoint.hostname, endpoint.port or 443
    for cipher in REQUIRED_TLS12_CIPHERS:
        ssl_ctx = create_ssl_context(
            ca_cert=os.environ.get('TLS_CA_CERT'),
            client_cert=os.environ.get('TLS_CLIENT_CERT'),
            client_key=os.environ.get('TLS_CLIENT_KEY'),
            check_hostname=False,
        )
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.set_ciphers(cipher)

        try:
            _, writer = await asyncio.open_connection(host, port, ssl=ssl_ctx, server_hostname=host)
        except Exception as exc:
            pytest.fail(f"Required TLS 1.2 cipher suite not supported: {cipher}, error={exc}")

        try:
            negotiated = writer.get_extra_info('ssl_object').cipher()[0]
            assert negotiated == cipher, f"Expected cipher suite {cipher}, negotiated {negotiated}"
        finally:
            writer.close()
            with contextlib.suppress(ConnectionError, ssl.SSLError):
                await writer.wait_closed()


@pytest.mark.asyncio
async def test_tc_087():
    # Step 3 validation, cipher suites. A handshake negotiates one suite, so each required suite gets a TLS
    # handshake of its own (steps 1-4), terminated before any HTTP upgrade. These run before the connection
    # that goes through steps 1-10.
    await assert_tls12_cipher_suites_supported(f'{CSMS_ADDRESS}/{SP3_CP}')

    # Create SSL context for mTLS connection (SP3: server + client cert)
    ssl_ctx = create_ssl_context(
        ca_cert=os.environ.get('TLS_CA_CERT'),
        client_cert=os.environ.get('TLS_CLIENT_CERT'),
        client_key=os.environ.get('TLS_CLIENT_KEY'),
        check_hostname=False,
    )

    # Step 1-6: TLS handshake with client cert + WebSocket upgrade (no BasicAuth for SP3)
    ws = await websockets.connect(
        uri=f'{CSMS_ADDRESS}/{SP3_CP}',
        subprotocols=['ocpp1.6'],
        ssl=ssl_ctx,
    )
    assert ws.open

    # Verify TLS version is 1.2 or above
    ssl_obj = ws.transport.get_extra_info('ssl_object')
    assert ssl_obj is not None
    tls_version = ssl_obj.version()
    assert tls_version in ('TLSv1.2', 'TLSv1.3')

    cp = TziChargePoint16(SP3_CP, ws)
    start_task = asyncio.create_task(cp.start())

    # Step 7-8: BootNotification
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 9-10: StatusNotification per connector
    for cid in (0, 1):
        await cp.send_status_notification(cid)

    start_task.cancel()
    await ws.close()
