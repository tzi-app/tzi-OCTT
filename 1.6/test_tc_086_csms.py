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
    - This test only covers security profile 2 (basic auth + server-side TLS). SP3 (mutual TLS with client
      certificates) is not covered here.
    - The cipher suite validation checks that the negotiated cipher is one of the required set, but cannot
      verify that ALL four cipher suites are simultaneously supported from a single connection.
    - The commonName RDN is validated for existence but NOT compared against the actual server FQDN.
      check_hostname=False is used because the test environment may use localhost/IP rather than a real FQDN.
      A production-grade validation would compare the CN value against the hostname from CSMS_ADDRESS.

Ambiguities in the test case document:
    - Step 9: "[Send per connector and connectorId=0.]" — unclear whether this means "for each connector
      including connectorId=0" or "for each connector starting at connectorId=0". Implementation sends
      StatusNotification for connectorId=0 (charge point) and connectorId=1 (single physical connector).
      The number of physical connectors is not specified in the test case.
"""

import asyncio
import os
import pytest
import websockets

from ocpp.v16.enums import RegistrationStatus

from charge_point import TziChargePoint16
from utils import (create_ssl_context, get_basic_auth_headers, get_tls_info,
                    validate_cert_key_size, validate_cert_x509_pem)

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ADDRESS = os.environ['CSMS_ADDRESS']


@pytest.mark.asyncio
async def test_tc_086():
    # Create SSL context for TLS connection (SP2: server cert only)
    ssl_ctx = create_ssl_context(
        ca_cert=os.environ.get('TLS_CA_CERT'),
        check_hostname=False,
    )

    # Step 1-6: TLS handshake + WebSocket upgrade with basic auth
    ws = await websockets.connect(
        uri=f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}',
        subprotocols=['ocpp1.6'],
        ssl=ssl_ctx,
        extra_headers=get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD),
    )
    assert ws.open

    # Tool Validation (Step 2): TLS version, cipher, certificate checks
    tls_info = get_tls_info(ws)
    assert tls_info is not None

    # TLS version must be 1.2 or above
    assert tls_info['tls_version'] in ('TLSv1.2', 'TLSv1.3'), \
        f"Expected TLS 1.2+, got {tls_info['tls_version']}"

    # Verify negotiated cipher is from the required set
    REQUIRED_CIPHERS = {
        # TLS 1.2 IANA names
        'TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256',
        'TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384',
        'TLS_RSA_WITH_AES_128_GCM_SHA256',
        'TLS_RSA_WITH_AES_256_GCM_SHA384',
        # TLS 1.2 OpenSSL names
        'ECDHE-ECDSA-AES128-GCM-SHA256',
        'ECDHE-ECDSA-AES256-GCM-SHA384',
        'AES128-GCM-SHA256',
        'AES256-GCM-SHA384',
        # TLS 1.3 cipher suites (same AES-GCM algorithms).
        # Not part of the OCPP 1.6 Security Whitepaper (which predates TLS 1.3),
        # but accepted here: TLS 1.3 is strictly more secure and rejecting it
        # would prevent legitimate security hardening by CSMS operators.
        'TLS_AES_128_GCM_SHA256',
        'TLS_AES_256_GCM_SHA384',
    }
    cipher_name = tls_info['cipher'][0]
    assert cipher_name in REQUIRED_CIPHERS, \
        f"Negotiated cipher '{cipher_name}' not in required set"

    # Validate certificate key size (RSA/DSA >= 2048 bits, ECC >= 224 bits)
    der_cert = tls_info['peer_cert_der']
    validate_cert_key_size(der_cert)

    # Validate certificate is valid X.509 in PEM format
    validate_cert_x509_pem(der_cert)

    # Validate certificate has a serial number
    from cryptography.x509 import load_der_x509_certificate
    cert = load_der_x509_certificate(der_cert)
    assert cert.serial_number is not None and cert.serial_number > 0, \
        "Certificate must include a serial number"

    # Validate commonName RDN contains the FQDN of the server
    from cryptography.x509.oid import NameOID
    cn_attrs = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    assert len(cn_attrs) > 0, "Certificate subject must contain a commonName RDN"

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
