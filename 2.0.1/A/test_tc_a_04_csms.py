"""
Test case name      TLS - server-side certificate - Valid certificate
Test case Id        TC_A_04_CSMS
Use case Id(s)      A00
Requirement(s)      A00.FR.306, A00.FR.307, A00.FR.312, A00.FR.318, A00.FR.321, A00.FR.502, A00.FR.503, A00.FR.507,
                    A00.FR.508, A00.FR.510

Requirement Details:
    A00.FR.306: The CSMS SHALL act as the TLS server.
    A00.FR.307: The CSMS SHALL authenticate itself by using the CSMS certificate as server side certificate.
    A00.FR.312: The communication channel SHALL be secured using Transport Layer Security (TLS) [4].
    A00.FR.318: The CSMS SHALL support at least the following four cipher suites: TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384 TLS_RSA_WITH_AES_128_GCM_SHA256 TLS_RSA_WITH_AES_256_GCM_SHA384 Note: The CSMS will have to provide 2 different certificates to support both cipher suites. Also when using security profile 3, the CSMS should be capable of generating client side certificates for both cipher suites.
    A00.FR.321: The TLS Server and Client SHALL NOT use TLS compression methods to avoid compression side-channel attacks and to ensure interoperability as described in Section 6 of [10].
    A00.FR.502: A00.FR.501 AND RSA or DSA
        Precondition: A00.FR.501 AND RSA or DSA
    A00.FR.503: A00.FR.501 AND elliptic curve cryptography
        Precondition: A00.FR.501 AND elliptic curve cryptography
    A00.FR.507: The certificates SHALL be stored and transmitted in the X.509 format encoded in Privacy-Enhanced Mail (PEM) format.
    A00.FR.508: All certificates SHALL include a serial number.
    A00.FR.510: For the CSMS certificate, the subject field SHALL match the FQDN of the endpoint of the server in the CN (commonName) RDN.
System under test   CSMS

Description         The CSMS uses a server-side certificate to identify itself to the Charging Station, when using
                    security profile 2 or 3.

Purpose             To verify whether the CSMS is able to provide a valid server certificate and setup a secured
                    WebSocket connection.

Prerequisite(s)     The CSMS supports security profile 2 and/or 3

Test Scenario
1. The OCTT terminates the connection and initiates a TLS handshake and sends a Client Hello to the CSMS.
2. The CSMS responds with a Server Hello with the <Configured server certificate>
3. The OCTT performs the following actions:
    Send client certificate
    Client Key Exchange
    Certificate verify
    Change Cipher Spec
    Finished

    Note(s):
    - The client certificate is only sent when the CSMS uses security profile 3.

4. The CSMS performs the following actions:
    Change Cipher Spec
    Finished

5. The OCTT sends a HTTP upgrade request to the CSMS
    Note(s):
    - The HTTP request only contains a username/password combination when the CSMS uses security profile 2.

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
    - When using RSA or DSA the key must be at least 2048 bits long.
    and when using elliptic curve cryptography the key must be at least 224 bits long.
    - The received server side certificate must be transmitted in the X.509 format encoded in
      Privacy-Enhanced Mail (PEM) format.
    - The certificate must include a serial number.
    - The subject field of the certificate must contain a commonName RDN which consists of the FQDN of
      the endpoint of the server.

* Step 8:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a


NOTE: TC_A_04_CSMS mandates static RSA cipher suites
      (TLS_RSA_WITH_AES_128_GCM_SHA256, TLS_RSA_WITH_AES_256_GCM_SHA384).
      The OCPP 2.0.1 spec recommends ECDHE over RSA for forward secrecy,
      yet still requires these for certification. A CSMS that rejects static
      RSA is arguably more secure — but will fail this test.
"""

import asyncio
import os
import time
import logging
import ssl
from urllib.parse import urlparse

import pytest
import websockets

from ocpp.v201.enums import RegistrationStatusEnumType, ConnectorStatusEnumType

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, create_ssl_context, get_tls_info, validate_cert_key_size, validate_cert_x509_pem

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
TLS_CA_CERT = os.environ['TLS_CA_CERT']
TLS_CLIENT_CERT = os.environ['TLS_CLIENT_CERT']
TLS_CLIENT_KEY = os.environ['TLS_CLIENT_KEY']
SECURITY_PROFILE_2_CP = os.environ['SECURITY_PROFILE_2_CP_A']
SECURITY_PROFILE_3_CP = os.environ['SECURITY_PROFILE_3_CP_A']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

ACCEPTABLE_TLS_VERSIONS = {'TLSv1.2', 'TLSv1.3'}
REQUIRED_TLS12_CIPHERS = (
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'AES128-GCM-SHA256',
    'AES256-GCM-SHA384',
)


async def assert_tls12_cipher_supported(uri, headers, security_profile):
    for cipher in REQUIRED_TLS12_CIPHERS:
        ssl_ctx = create_ssl_context(
            ca_cert=TLS_CA_CERT,
            client_cert=TLS_CLIENT_CERT if security_profile == 3 else None,
            client_key=TLS_CLIENT_KEY if security_profile == 3 else None,
        )
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.set_ciphers(cipher)

        try:
            ws = await websockets.connect(
                uri=uri,
                subprotocols=['ocpp2.0.1'],
                extra_headers=headers,
                ssl=ssl_ctx,
            )
            await ws.close()
        except Exception as exc:
            pytest.fail(f"Required TLS 1.2 cipher not supported: {cipher}, error={exc}")


@pytest.mark.asyncio
@pytest.mark.parametrize("security_profile", [2, 3])
async def test_tc_a_04(security_profile):
    if security_profile == 2:
        cp_id = SECURITY_PROFILE_2_CP
        ssl_ctx = create_ssl_context(ca_cert=TLS_CA_CERT)
        headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)
    else:
        cp_id = SECURITY_PROFILE_3_CP
        ssl_ctx = create_ssl_context(
            ca_cert=TLS_CA_CERT,
            client_cert=TLS_CLIENT_CERT,
            client_key=TLS_CLIENT_KEY,
        )
        headers = {}

    uri = f'{CSMS_ADDRESS}/{cp_id}'
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )

    time.sleep(0.5)

    # Validate TLS properties
    tls_info = get_tls_info(ws)
    assert tls_info is not None, "TLS info should be available on a WSS connection"

    # TLS version must be 1.2 or above
    assert tls_info['tls_version'] in ACCEPTABLE_TLS_VERSIONS, \
        f"TLS version must be 1.2 or above, got {tls_info['tls_version']}"

    # Cipher must use at least 128-bit keys
    cipher_name, cipher_protocol, cipher_bits = tls_info['cipher']
    assert cipher_bits >= 128, \
        f"Cipher must use at least 128-bit keys, got {cipher_bits}"

    # Peer certificate must have serialNumber and commonName
    peer_cert = tls_info['peer_cert']
    assert peer_cert is not None, "Peer certificate must be present"

    subject = dict(x[0] for x in peer_cert.get('subject', ()))
    assert 'commonName' in subject, "Certificate subject must contain commonName"
    assert peer_cert.get('serialNumber'), "Certificate must include a serial number"
    server_host = urlparse(uri).hostname
    assert subject.get('commonName') == server_host, \
        f"Certificate commonName must match endpoint FQDN ({server_host}), got {subject.get('commonName')}"

    # Validate certificate public key size (RSA/DSA >= 2048, ECC >= 224)
    peer_cert_der = tls_info['peer_cert_der']
    key_size = validate_cert_key_size(peer_cert_der)

    # Validate X.509 PEM format
    validate_cert_x509_pem(peer_cert_der)

    logging.info(f"TLS: version={tls_info['tls_version']}, cipher={cipher_name}, "
                 f"bits={cipher_bits}, key_size={key_size}, CN={subject.get('commonName')}, "
                 f"serial={peer_cert.get('serialNumber')}")

    await assert_tls12_cipher_supported(uri=uri, headers=headers, security_profile=security_profile)

    # Boot + Status + NotifyEvent
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
