"""
Test case name      Upgrade Charge Point Security Profile - Accepted
Test case Id        TC_083_CSMS
Section             3.21 Security / 3.21.1 Secure connection setup
Document ref        Table 194, pages 167-169 (CompliancyTestTool-TestCaseDocument 2025-11)
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
"""

import asyncio
import os
import pytest
import websockets
from websockets import InvalidStatusCode

from ocpp.v16.enums import RegistrationStatus, ResetType

from charge_point import TziChargePoint16
from utils import create_ssl_context, get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
CSMS_WSS_ADDRESS = os.environ.get('CSMS_WSS_ADDRESS', 'wss://localhost:8082')


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_083(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ChangeConfiguration.req for SecurityProfile
    await asyncio.wait_for(cp._received_change_configuration.wait(), timeout=ACTION_TIMEOUT)
    assert cp._change_configuration_key == 'SecurityProfile'
    assert cp._change_configuration_value in ('2', '3')

    # Step 3-4: Wait for CSMS to send Reset.req (Hard)
    await asyncio.wait_for(cp._received_reset.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reset_type == ResetType.hard

    start_task.cancel()
    await connection.close()

    # Step 5-6: Reconnect with higher security profile (TLS/WSS)
    ssl_ctx = create_ssl_context(
        ca_cert=os.environ.get('TLS_CA_CERT'),
        client_cert=os.environ.get('TLS_CLIENT_CERT'),
        client_key=os.environ.get('TLS_CLIENT_KEY'),
        check_hostname=False,
    )
    ws = await websockets.connect(
        uri=f'{CSMS_WSS_ADDRESS}/{BASIC_AUTH_CP}',
        subprotocols=['ocpp1.6'],
        ssl=ssl_ctx,
        extra_headers=get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD),
    )
    assert ws.open

    cp2 = TziChargePoint16(BASIC_AUTH_CP, ws)
    start_task2 = asyncio.create_task(cp2.start())

    # Step 7-8: BootNotification
    boot_response = await cp2.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 9-10: StatusNotification(Available) per connector and connectorId=0
    for cid in (0, 1):
        await cp2.send_status_notification(cid)

    start_task2.cancel()
    await ws.close()

    # Step 11-12: Reconnect with old security profile — CSMS rejects
    try:
        old_ws = await websockets.connect(
            uri=f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}',
            subprotocols=['ocpp1.6'],
            extra_headers=get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD),
        )
        # If connection succeeded, the CSMS should have rejected it
        await old_ws.close()
        pytest.fail("CSMS should have rejected connection with old security profile")
    except (InvalidStatusCode, Exception):
        pass  # Expected: connection rejected

    # Step 13-14: Reconnect with higher security profile (restore connection)
    ws2 = await websockets.connect(
        uri=f'{CSMS_WSS_ADDRESS}/{BASIC_AUTH_CP}',
        subprotocols=['ocpp1.6'],
        ssl=ssl_ctx,
        extra_headers=get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD),
    )
    assert ws2.open
    await ws2.close()
