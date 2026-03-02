"""
Test case name      Basic Authentication - Invalid password
Test case Id        TC_A_03_CSMS
Use case Id(s)      A00
Requirement(s)      A00.FR.204

Requirement Details:
    A00.FR.204: When the Charging Station receives a BootNotificationRequest, the CSMS SHALL respond with a BootNotificationResponse.
        Precondition: A00.FR.203
System under test   CSMS

Description         The Charging Station uses Basic authentication to authenticate itself to the CSMS, when using security
                    profile 1 or 2.

Purpose             To verify whether the CSMS is able to validate the (invalid) Basic authentication credentials provided by the
                    Charging Station at the connection request.
Prerequisite(s)     The CSMS supports security profile 1 and/or 2

Test Scenario
1. The OCTT sends a HTTP upgrade request without an Authorization header.
2. The CSMS rejects the connection upgrade request.
3. The OCTT sends a HTTP upgrade request with an Authorization header, containing a username/password combination.
4. The CSMS validates the username/password combination AND rejects the connection upgrade request.
"""

import os
import string
import random
import pytest
import websockets
from websockets import InvalidStatusCode
from utils import get_basic_auth_headers, build_default_ssl_context

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP_A']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ADDRESS = os.environ['CSMS_ADDRESS']


def _generate_random_password(min_len=16, max_len=40):
    """Generate a random identifierString with high entropy (16-40 alphanumeric + special chars)."""
    allowed_chars = string.ascii_letters + string.digits + ".*-_:+!@#$%^&"
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(allowed_chars, k=length))


async def _expect_http_upgrade_rejected(headers):
    uri = f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}'
    ssl_ctx = build_default_ssl_context() if uri.startswith('wss://') else None
    with pytest.raises(InvalidStatusCode) as exc:
        await websockets.connect(
            uri=uri,
            subprotocols=['ocpp2.0.1'],
            extra_headers=headers,
            ssl=ssl_ctx,
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_tc_a_03():
    # Step 1-2: Upgrade request without Authorization header is rejected.
    await _expect_http_upgrade_rejected(headers={})

    # Step 3-4: Upgrade request with invalid password is rejected.
    # Per spec: password must be a randomly chosen identifierString with
    # sufficiently high entropy, consisting of minimum 16 and maximum 40 characters.
    random_invalid_password = _generate_random_password()
    invalid_headers = get_basic_auth_headers(BASIC_AUTH_CP, random_invalid_password)
    await _expect_http_upgrade_rejected(headers=invalid_headers)
