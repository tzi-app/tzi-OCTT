"""
Test case name      TLS - server-side certificate - Valid certificate
Test case Id        TC_A_04_CSMS
Use case Id(s)      A00
Requirement(s)      A00.FR.306, A00.FR.307, A00.FR.312, A00.FR.318, A00.FR.321, A00.FR.502, A00.FR.503,
                    A00.FR.507, A00.FR.508, A00.FR.510

Requirement Details:
    A00.FR.306: The CSMS SHALL act as the TLS server.
    A00.FR.307: The CSMS SHALL authenticate itself by using the CSMS certificate as server side certificate.
    A00.FR.312: The communication channel SHALL be secured using Transport Layer Security (TLS) [4].
    A00.FR.318: The CSMS SHALL support at least the following four cipher suites:
                TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
                TLS_RSA_WITH_AES_128_GCM_SHA256 TLS_RSA_WITH_AES_256_GCM_SHA384 Note: The CSMS will have to
                provide 2 different certificates to support both cipher suites. Also when using security
                profile 3, the CSMS should be capable of generating client side certificates for both cipher
                suites.
    A00.FR.321: The TLS Server and Client SHALL NOT use TLS compression methods to avoid compression
                side-channel attacks and to ensure interoperability as described in Section 6 of [10].
    A00.FR.502: This translates into a key that SHALL be at least 2048 bits long.
        Precondition: A00.FR.501 AND RSA or DSA
    A00.FR.503: This translates into a key that SHALL be at least 224 bits long.
        Precondition: A00.FR.501 AND elliptic curve cryptography
    A00.FR.507: The certificates SHALL be stored and transmitted in the X.509 format encoded in
                Privacy-Enhanced Mail (PEM) format.
    A00.FR.508: All certificates SHALL include a serial number.
    A00.FR.510: For the CSMS certificate, the subject field SHALL match the FQDN of the endpoint of the server
                in the CN (commonName) RDN.
System under test   CSMS

Description         The CSMS uses a server-side certificate to identify itself to the Charging Station, when
                    using security profile 2 or 3.

Purpose             To verify whether the CSMS is able to provide a valid server certificate and setup a
                    secured WebSocket connection.

Prerequisite(s)     The CSMS supports security profile 2 and/or 3

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System terminates the connection and initiates a TLS handshake and sends a Client Hello to the
   CSMS.
2. The CSMS responds with a Server Hello
    With the <Configured server certificate>
3. The Test System performs the following actions:
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
5. The Test System sends a HTTP upgrade request to the CSMS
    Note(s):
    - The HTTP request only contains a username/password combination when the CSMS uses security profile 2.
6. The CSMS upgrades the connection to a (secured) WebSocket connection.
7. The Test System sends a BootNotificationRequest
    with reason PowerUp
    chargingStation.model <Configured model>
    chargingStation.vendorName <Configured vendorName>
8. The CSMS responds with a BootNotificationResponse
9. The Test System notifies the CSMS about the current state of all connectors.
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
    The Test System validates the following before finishing the TLS handshake:
    - The CSMS must use TLS version 1.2 or above
    At least the following set of cipher suites must be supported:
    TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    AND
    TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    AND
    TLS_RSA_WITH_AES_128_GCM_SHA256
    AND
    TLS_RSA_WITH_AES_256_GCM_SHA384
    - When using RSA or DSA the key must be at least 2048 bits long.
    and when using elliptic curve cryptography the key must be at least 224 bits long.
    - The received server side certificate must be transmitted in the X.509 format encoded in Privacy-Enhanced
      Mail (PEM) format.
    - The certificate must include a serial number.
    - The subject field of the certificate must contain a commonName RDN which consists of the FQDN of the
      endpoint of the server.
    NOTE: If one of the above validations fails, the Test System can still proceed with the next steps of the
          testcase (if it is able to), but the testcase will FAIL and the Test System reports why it failed.

* Step 8:
    Message: BootNotificationResponse
    with status Accepted

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.3. Page 24 - (2026-02) - A00.FR.308 - Additional requirement references
        (Part 2 errata - applies to this test via use case A00)
        |  | ID | Precondition | Requirement definition | Note |
        | Old | A00.FR.308 |  | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3]. |  |
        | New | A00.FR.308 |  | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3] and Section 4 of
          [26] |  |

    2.4. Page 26 - (2026-02) - A00.FR.403 - Additional requirement references
        (Part 2 errata - applies to this test via use case A00)
        | | ID | Precondition | Requirement definition | Note |
        | Old | A00.FR.403 | | The CSMS SHALL verify the certification path of the Charging Station’s
          certificate according to the path validation rules established in Section 6 of [3] | |
        | New | A00.FR.403 | | The CSMS SHALL verify the certification path of the Charging Station’s
          certificate according to the path validation rules established in Section 6 of [3] and Section 4 of
          [26] | |

    2.6. Page 27 - (2026-02) - A00.FR.411 - Additional requirement references
        (Part 2 errata - applies to this test via use case A00)
        | | ID | Precondition | Requirement definition | Note |
        | Old | A00.FR.411 | | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3]. (Same as
          A00.FR.308) | |
        | New | A00.FR.411 | | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3] and Section 4 of
          [26]. (Same as A00.FR.308) | |
"""

import asyncio
import logging
import os

import pytest

from charge_point import TziChargePoint21
from security import (
    ACCEPTABLE_TLS_VERSIONS,
    assert_tls12_ciphers_supported,
    connect_with_profile,
    csms_host,
    validate_server_certificate,
)
from utils import get_tls_info

SECURITY_PROFILE_2_CP = os.environ['CP21_SP2']
SECURITY_PROFILE_3_CP = os.environ['CP21_SP3']


@pytest.mark.asyncio
@pytest.mark.parametrize("security_profile", [2, 3])
async def test_tc_a_04(security_profile):
    cp_id = SECURITY_PROFILE_2_CP if security_profile == 2 else SECURITY_PROFILE_3_CP

    # Step 3 validation, cipher suites (A00.FR.318). A handshake negotiates one suite, so
    # each required TLS 1.2 suite gets a TLS handshake of its own: steps 1-4 with the step 3
    # validations, after which the connection is terminated before any HTTP upgrade. These
    # handshakes run before the connection that goes through steps 1-10.
    await assert_tls12_ciphers_supported(security_profile, validate_certificate=True)

    # 1-4. TLS handshake. The client certificate is only sent when the CSMS uses security
    #      profile 3.
    # 5.   The Test System sends a HTTP upgrade request to the CSMS. It only contains a
    #      username/password combination when the CSMS uses security profile 2.
    # 6.   The CSMS upgrades the connection to a (secured) WebSocket connection.
    ws = await connect_with_profile(cp_id, security_profile)
    try:
        # Step 3 validations on this handshake
        tls_info = get_tls_info(ws)
        assert tls_info is not None, "TLS info should be available on a WSS connection"

        # The CSMS must use TLS version 1.2 or above
        assert tls_info['tls_version'] in ACCEPTABLE_TLS_VERSIONS, \
            f"TLS version must be 1.2 or above, got {tls_info['tls_version']}"

        # Server certificate: key size, X.509 in PEM, serial number, commonName is the FQDN
        common_name, serial, key_size = validate_server_certificate(
            tls_info['peer_cert'], tls_info['peer_cert_der'], csms_host())
        logging.info(f"TLS: version={tls_info['tls_version']}, cipher={tls_info['cipher'][0]}, "
                     f"key_size={key_size}, CN={common_name}, serial={serial}")

        cp = TziChargePoint21(cp_id, ws)
        start_task = asyncio.create_task(cp.start())

        # 7. The Test System sends a BootNotificationRequest with reason PowerUp, the
        #    configured model and the configured vendorName
        # 8. The CSMS responds with a BootNotificationResponse with status Accepted
        boot_response = await cp.send_boot_notification(reason='PowerUp')
        assert boot_response.status == 'Accepted', \
            f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

        # 9.  The Test System notifies the CSMS about the current state of all connectors.
        #     StatusNotificationRequest - connectorStatus Available
        #     NotifyEventRequest - trigger Delta, actualValue "Available",
        #                          component.name "Connector", variable.name "AvailabilityState"
        # 10. The CSMS responds accordingly.
        await cp.send_all_connectors_status('Available')

        start_task.cancel()
    finally:
        await ws.close()
