"""
Test case name      Upgrade Charge Point Security Profile - Accepted
Test case Id        TC_083_CSMS
Section             3.21 Security / 3.21.1 Secure connection setup
Document ref        CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, Table 194,
                    document pages 167-169 (2025-11)
System under test   Central System

Description         The Central System can upgrade the connection using a higher Security Profile, the Central System can
                    send a new value for the SecurityProfile Configuration key.

Purpose             To verify if the Central System is able to upgrade the Charge Point to a higher security profile than currently
                    configured.

Prerequisite(s)     - Next to security profile 2, also security profile 1 and/or 3 must be supported.
                    - Security profile must be set to 1 or 2.

Before (Preparations)
    Configuration State: N/a
    Memory State:
        - CertificateInstalled if SecurityProfile is 1.
        - RenewChargePointCertificate if SecurityProfile is 2.
    Reusable State(s): N/a

Test Scenario
    Manual Action: Send a ChangeConfiguration request for SecurityProfile on the Central System.

    1. The Central System sends a ChangeConfiguration.req
    2. The Charge Point responds with a ChangeConfiguration.conf

    Manual Action: Send a Reset request of type Hard on the Central System.

    3. The Central System sends a Reset.req
    4. The Charge Point responds with a Reset.conf

    5. The Charge Point reconnects to the Central System with security profile is <Configured securityProfile + 1>
    6. The Central System accepts the connection attempt.

    7. The Charge Point sends a BootNotification.req
    8. The Central System responds with a BootNotification.conf

    [Send per connector and connectorId=0]
    9. The Charge Point sends a StatusNotification.req
    10. The Central System responds with a StatusNotification.conf

    11. The Charge Point reconnects to the Central System with security profile is <Configured securityProfile>
    12. The Central System shall not accept the connection attempt.

    13. The Charge Point reconnects to the Central System with security profile is <Configured securityProfile + 1>
    14. The Central System accepts the connection attempt.

    Note(s):
    - Steps 13-14 are done to restore the connection before ending the testcase.

Tool Validations
    * Step 1:
        (Message: ChangeConfiguration.req)
        - key is SecurityProfile
        - value is <One level higher than the configured security profile>

    * Step 2:
        (Message: ChangeConfiguration.conf)
        - status should be Accepted

    * Step 3:
        (Message: Reset.req)
        - type is Hard

    * Step 4:
        (Message: Reset.conf)
        - status should be Accepted

    * Step 8:
        (Message: BootNotification.conf)
        - status is Accepted

    * Step 9:
        (Message: StatusNotification.req)
        - status should be Available

    * Step 12:
        When upgrading a Charge Point to a higher security profile, a Central System has several options
        regarding which endpoint to use. This affects the way the Central System is able to detect it needs
        to reject the incoming connection attempt.

        In case of having upgraded from security profile 2 to 3, but there is an incoming connection attempt
        using security profile 2:
        - When the same endpoint is used, then it depends on the Central System endpoint configuration.
          - When the Central System does a full switch and only allows TLS handshakes when a client certificate
            is provided, then the TLS handshake is rejected.
          - When the Central System only requires this Charge Point to use a client certificate, then it accepts
            the TLS handshake (because it will be unable to detect which Charge Point is connecting) and it
            rejects the HTTP request to establish the WebSocket connection.
        - When a different port or a whole different endpoint is used for the upgrade, then on the original
          endpoint the Central System accepts the TLS handshake and it rejects the HTTP request to establish
          the WebSocket connection (because this Charge Point is not allowed to connect with security profile 2
          anymore).

        In case of security profile 1, the case is always the same. The Central System shall always reject the
        HTTP request to establish the WebSocket connection, because TLS is required for this Charge Point.

Expected result(s) / behaviour:
    The Charge Point and the Central System are connected.

Implementation notes:
    - Implements the security profile 2 -> 3 path. The Charge Point is CP16_SP2, configured at the Central
      System with security profile 2.
      - Its Charge Point certificate (memory state RenewChargePointCertificate) is certs/client.pem.
      - A security profile 2 connection is TLS with the server certificate only, with the username/password
        in the HTTP request.
      - A security profile 3 connection is TLS with the client certificate and no username/password.
    - Step 12 passes when the Central System rejects the TLS handshake or the HTTP request, as described in
      its validation. If the attempt fails in the test's own TLS setup (for example, the server certificate
      is not trusted), it never reached the Central System, so the test fails instead.
    - Step 9 assumes a single physical connector (connectorId=0 and connectorId=1).
"""

import asyncio
import logging
import os
import ssl

import pytest
import websockets
from websockets import InvalidStatusCode

from ocpp.v16.enums import ChargePointStatus, RegistrationStatus, ResetType

from charge_point import TziChargePoint16
from utils import create_ssl_context, get_basic_auth_headers
from trigger import trigger_v16

SP2_CP = os.environ['CP16_SP2']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CSMS_ADDRESS = os.environ['CSMS_ADDRESS']

CONFIGURED_SECURITY_PROFILE = 2


async def connect_with_security_profile_2():
    """TLS with the server certificate only; the HTTP request carries the username/password."""
    return await websockets.connect(
        uri=f'{CSMS_ADDRESS}/{SP2_CP}',
        subprotocols=['ocpp1.6'],
        ssl=create_ssl_context(ca_cert=os.environ.get('TLS_CA_CERT'), check_hostname=False),
        extra_headers=get_basic_auth_headers(SP2_CP, TEST_USER_PASSWORD),
    )


async def connect_with_security_profile_3():
    """TLS with the Charge Point certificate; the HTTP request has no username/password."""
    return await websockets.connect(
        uri=f'{CSMS_ADDRESS}/{SP2_CP}',
        subprotocols=['ocpp1.6'],
        ssl=create_ssl_context(
            ca_cert=os.environ.get('TLS_CA_CERT'),
            client_cert=os.environ.get('TLS_CLIENT_CERT'),
            client_key=os.environ.get('TLS_CLIENT_KEY'),
            check_hostname=False,
        ),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(SP2_CP, get_basic_auth_headers(SP2_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_083(connection):
    # The Charge Point is connected with its configured security profile 2.
    assert connection.open
    cp = TziChargePoint16(SP2_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: ChangeConfiguration.req for SecurityProfile, one level higher than configured
    asyncio.create_task(trigger_v16(SP2_CP, 'change-configuration', {
        'key': 'SecurityProfile',
        'value': str(CONFIGURED_SECURITY_PROFILE + 1),
    }))
    await asyncio.wait_for(cp._received_change_configuration.wait(), timeout=ACTION_TIMEOUT)
    assert cp._change_configuration_key == 'SecurityProfile'
    assert cp._change_configuration_value == str(CONFIGURED_SECURITY_PROFILE + 1)

    # Step 3-4: Reset.req of type Hard; the Charge Point has answered Accepted when the event is set
    asyncio.create_task(trigger_v16(SP2_CP, 'reset', {'type': 'Hard'}))
    await asyncio.wait_for(cp._received_reset.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reset_type == ResetType.hard

    start_task.cancel()
    await connection.close()

    # Step 5-6: Reconnect with security profile 3; the Central System accepts it
    ws = await connect_with_security_profile_3()
    assert ws.open
    cp2 = TziChargePoint16(SP2_CP, ws)
    start_task2 = asyncio.create_task(cp2.start())

    # Step 7-8: BootNotification
    boot_response = await cp2.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 9-10: StatusNotification (Available) per connector and connectorId=0
    for cid in (0, 1):
        await cp2.send_status_notification(cid, status=ChargePointStatus.available)

    start_task2.cancel()
    await ws.close()

    # Step 11-12: Reconnect with security profile 2; the Central System rejects the TLS handshake
    # or the HTTP request
    try:
        old_ws = await connect_with_security_profile_2()
    except InvalidStatusCode as exc:
        logging.info(f"Central System rejected the HTTP request: {exc}")
    except ssl.SSLCertVerificationError as exc:
        pytest.fail(f"The test could not verify the Central System's server certificate, so the "
                    f"connection attempt never reached the Central System: {exc}")
    except (ssl.SSLError, ConnectionError) as exc:
        logging.info(f"Central System rejected the TLS handshake: {exc}")
    else:
        await old_ws.close()
        pytest.fail("Central System accepted a connection with security profile 2 after the upgrade to 3")

    # Step 13-14: Reconnect with security profile 3 to restore the connection
    ws2 = await connect_with_security_profile_3()
    assert ws2.open
    await ws2.close()
