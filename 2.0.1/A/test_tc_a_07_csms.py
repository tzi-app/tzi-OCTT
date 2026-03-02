"""
Test case name      TLS - Client-side certificate - valid certificate
Test case Id        TC_A_07_CSMS
Use case Id(s)      A00
Requirement(s)      A00.FR.409, A00.FR.410, A00.FR.415, A00.FR.416, A00.FR.421

Requirement Details:
    A00.FR.409: The CSMS SHALL act as the TLS server. (Same as A00.FR.306)
    A00.FR.410: The CSMS SHALL authenticate itself by using the CSMS certificate as server side certificate. (Same as A00.FR.307)
    A00.FR.415: The communication channel SHALL be secured using Transport Layer Security (TLS) [4]. (Same as A00.FR.312)
    A00.FR.416: The Charging Station and CSMS SHALL only use TLS v1.2 or above. (Same as A00.FR.313)
    A00.FR.421: The CSMS SHALL support at least the following four cipher suites: TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384 TLS_RSA_WITH_AES_128_GCM_SHA256 TLS_RSA_WITH_AES_256_GCM_SHA384 (Same as A00.FR.318) Note: The CSMS will have to provide 2 different certificates to support both cipher suites. Also when using security profile 3, the CSMS should be capable of generating client side certificates for both cipher suites.
System under test   CSMS

Description         The Charging Station uses a client-side certificate to identify itself to the CSMS, when using
                    security profile 3.

Purpose             To verify whether the CSMS is able to receive a client certificate provided by a Charging Station
                    and setup a secured WebSocket connection.

Prerequisite(s)     The CSMS supports security profile 3

Test Scenario
1. The OCTT terminates the connection and initiates a TLS handshake and sends a Client Hello to the CSMS.
2. The CSMS responds with a Server Hello with the <Configured server certificate>
3. The OCTT performs the following actions:
    Send <Configured client certificate>
    Client Key Exchange
    Certificate verify
    Change Cipher Spec
    Finished
4. The CSMS performs the following actions:
    Change Cipher Spec
    Finished
5. The OCTT sends a HTTP upgrade request to the CSMS
6. The CSMS upgrades the connection to a (secured) WebSocket connection.
7. The OCTT sends a BootNotificationRequest with reason PowerUp
    chargingStation.model <Configured model>
    chargingStation.vendorName <Configured vendorName>
8. The CSMS responds with a BootNotificationResponse
9. The OCTT notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
10. The CSMS responds accordingly.

Tool validations
* Step 3:
    The OCTT validates the following before finishing the TLS handshake:
    - The CSMS must use TLS version 1.2 or above
    At least the following set of cipher suites must be supported:
    TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    AND TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    AND TLS_RSA_WITH_AES_128_GCM_SHA256
    AND TLS_RSA_WITH_AES_256_GCM_SHA384

* Step 8:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os
import time
import logging
import ssl

import pytest
import websockets

from ocpp.v201.enums import RegistrationStatusEnumType, ConnectorStatusEnumType

from tzi_charge_point import TziChargePoint
from utils import create_ssl_context, get_tls_info

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
TLS_CA_CERT = os.environ['TLS_CA_CERT']
TLS_CLIENT_CERT = os.environ['TLS_CLIENT_CERT']
TLS_CLIENT_KEY = os.environ['TLS_CLIENT_KEY']
SECURITY_PROFILE_3_CP = os.environ['SECURITY_PROFILE_3_CP_A']

ACCEPTABLE_TLS_VERSIONS = {'TLSv1.2', 'TLSv1.3'}
REQUIRED_TLS12_CIPHERS = (
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'AES128-GCM-SHA256',
    'AES256-GCM-SHA384',
)


async def assert_tls12_cipher_supported(uri):
    for cipher in REQUIRED_TLS12_CIPHERS:
        ssl_ctx = create_ssl_context(
            ca_cert=TLS_CA_CERT,
            client_cert=TLS_CLIENT_CERT,
            client_key=TLS_CLIENT_KEY,
        )
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.set_ciphers(cipher)

        try:
            ws = await websockets.connect(
                uri=uri,
                subprotocols=['ocpp2.0.1'],
                ssl=ssl_ctx,
            )
            await ws.close()
        except Exception as exc:
            pytest.fail(f"Required TLS 1.2 cipher not supported: {cipher}, error={exc}")


@pytest.mark.asyncio
async def test_tc_a_07():
    cp_id = SECURITY_PROFILE_3_CP

    # Step 1-6: Connect with valid client certificate (security profile 3 - no basic auth)
    ssl_ctx = create_ssl_context(
        ca_cert=TLS_CA_CERT,
        client_cert=TLS_CLIENT_CERT,
        client_key=TLS_CLIENT_KEY,
    )

    uri = f'{CSMS_ADDRESS}/{cp_id}'
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        ssl=ssl_ctx,
    )

    time.sleep(0.5)

    # Validate TLS properties
    tls_info = get_tls_info(ws)
    assert tls_info is not None, "TLS info should be available on a WSS connection"

    assert tls_info['tls_version'] in ACCEPTABLE_TLS_VERSIONS, \
        f"TLS version must be 1.2 or above, got {tls_info['tls_version']}"

    cipher_name, cipher_protocol, cipher_bits = tls_info['cipher']
    assert cipher_bits >= 128, \
        f"Cipher must use at least 128-bit keys, got {cipher_bits}"

    logging.info(f"TLS: version={tls_info['tls_version']}, cipher={cipher_name}, bits={cipher_bits}")
    await assert_tls12_cipher_supported(uri)

    # Step 7-10: Boot + Status + NotifyEvent
    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)
    await cp.send_notify_event([{
        'event_id': 1,
        'timestamp': '2024-01-01T00:00:00Z',
        'trigger': 'Delta',
        'actual_value': 'Available',
        'event_notification_type': 'HardWiredNotification',
        'component': {'name': 'Connector'},
        'variable': {'name': 'AvailabilityState'},
    }])

    start_task.cancel()
    await ws.close()
