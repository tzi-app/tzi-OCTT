"""
Test case name      Update Charge Point Password for HTTP Basic Authentication
Test case Id        TC_073_CSMS
Section             3.21.1. Secure connection setup
System under test   Central System
Document ref        Table 184, page 158-159/176 (OCPP Compliancy Testing Tool - TestCaseDocument, 2025-11)
                    PDF: CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, pages 55-56

Description         The Central System can configure a new password for HTTP Basic Authentication, the Central System can
                    send a new value for the BasicAuthPassword Configuration key.

Purpose             To check if the Central System is able to change the Basic Authentication password.

Prerequisite(s)     The Central System supports Security profile 1 and/or 2.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    Manual Action: Update the basic authentication password.

    1. The Central System sends a ChangeConfiguration.req
    2. The Charge Point responds with a ChangeConfiguration.conf

    3. The Charge Point disconnects its current connection and reconnects to the Central System
       using the provided password from step 1.

Tool Validations
    * Step 1:
        (Message: ChangeConfiguration.req)
        key is AuthorizationKey
        value contains the hex encoded representation of the basic authentication password
        the Charge Point needs to use when connecting to the Central System.
        Because it is advised to use a randomly generated binary to get maximal entropy,
        the tool only validates if the new password adheres to the OCPP password requirements:
        - The hexadecimal representation of the password has a maximum of 40 characters.
        - The length of the password must be between 16 and 20 bytes.

        NOTE: The docstring is ambiguous on whether the CP uses the hex string itself or the
        decoded bytes as the HTTP Basic Auth password. Per OCPP 1.6 convention, the hex string
        (AuthorizationKey value) is used directly as the password in the Authorization header.

    * Step 2:
        (Message: ChangeConfiguration.conf)
        status is Accepted

Expected result(s) / behaviour: n/a
"""

import asyncio
import os
import ssl
import pytest
import websockets

from charge_point import TziChargePoint16
from trigger import set_basic_auth_password, trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CSMS_ADDRESS = os.environ['CSMS_ADDRESS']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_073(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ChangeConfiguration.req
    trigger_task = asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'change-configuration', {
        'key': 'AuthorizationKey',
        'value': 'AABBCCDDEEFF00112233445566778899AABBCCDD',
    }))
    await asyncio.wait_for(cp._received_change_configuration.wait(), timeout=ACTION_TIMEOUT)

    # Verify the key is AuthorizationKey
    assert cp._change_configuration_key == 'AuthorizationKey'

    # Capture and validate the new password value (hex-encoded, 16-20 bytes → 32-40 hex chars)
    new_password = cp._change_configuration_value
    assert new_password is not None
    assert len(new_password) <= 40, f"Hex password too long: {len(new_password)} chars (max 40)"
    bytes.fromhex(new_password)  # raises ValueError if not valid hex
    byte_length = len(new_password) // 2
    assert 16 <= byte_length <= 20, f"Password length {byte_length} bytes, expected 16-20"

    # Wait for the CSMS to receive the CALLRESULT and update the stored password
    await asyncio.wait_for(trigger_task, timeout=ACTION_TIMEOUT)

    start_task.cancel()
    await connection.close()

    # Step 3: CP disconnects and reconnects with the new password
    ssl_ctx = None
    if CSMS_ADDRESS.startswith('wss://'):
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ca_cert = os.environ.get('TLS_CA_CERT')
        if ca_cert:
            ssl_ctx.load_verify_locations(ca_cert)
        else:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
    ws = await websockets.connect(
        uri=f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}',
        subprotocols=['ocpp1.6'],
        extra_headers=get_basic_auth_headers(BASIC_AUTH_CP, new_password),
        ssl=ssl_ctx,
    )
    assert ws.open
    await ws.close()

    # Restore original password so other tests are not affected
    await set_basic_auth_password(BASIC_AUTH_CP, TEST_USER_PASSWORD)
