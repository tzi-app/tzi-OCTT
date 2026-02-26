"""
Test case name      TLS - server-side certificate - Valid certificate
Test case Id        TC_086_CSMS
Section             3.21 Security / 3.21.1 Secure connection setup
System under test   Central System
Document ref        Table 196, pages 170-171 (CompliancyTestTool-TestCaseDocument, 2025-11)

Description         The Central System uses a server-side certificate to identify itself to the Charge Point, when using security
                    profile 2 or 3.

Purpose             To verify whether the Central System is able to provide a valid server certificate and setup a secured
                    WebSocket connection.

Prerequisite(s)     The Central System supports security profile 2 and/or 3.

Before (Preparations)
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): The OCTT closes the connection.

Test Scenario
    1. The Charge Point initiates a TLS handshake and sends a Client Hello to the Central System.
    2. The Central System responds with a Server Hello with the <Configured server certificate>

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

    Post scenario validations: N/a

Expected result(s) / behaviour: n/a
"""

import asyncio
import os
import ssl
import pytest
import websockets

from ocpp.v16.enums import RegistrationStatus

from charge_point import TziChargePoint16
from utils import create_ssl_context, get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_WSS_ADDRESS = os.environ.get('CSMS_WSS_ADDRESS', 'wss://localhost:8082')


@pytest.mark.asyncio
async def test_tc_086():
    # Create SSL context for TLS connection (SP2: server cert only)
    ssl_ctx = create_ssl_context(
        ca_cert=os.environ.get('TLS_CA_CERT'),
        check_hostname=False,
    )

    # Step 1-6: TLS handshake + WebSocket upgrade with basic auth
    ws = await websockets.connect(
        uri=f'{CSMS_WSS_ADDRESS}/{BASIC_AUTH_CP}',
        subprotocols=['ocpp1.6'],
        ssl=ssl_ctx,
        extra_headers=get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD),
    )
    assert ws.open

    # Verify TLS version is 1.2 or above
    ssl_obj = ws.transport.get_extra_info('ssl_object')
    assert ssl_obj is not None
    tls_version = ssl_obj.version()
    assert tls_version in ('TLSv1.2', 'TLSv1.3')

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
