"""
Test case name      Basic Authentication - Valid username/password combination
Test case Id        TC_085_CSMS
Section             3.21 Security > 3.21.1 Secure connection setup
System under test   Central System
Document ref        Table 195, document pages 169-170 (PDF pages 66-67 of Section 3)

Description         The Charge Point uses Basic authentication to authenticate itself to the Central System, when using
                    security profile 1 or 2.

Purpose             To verify whether the Central System is able to validate the (valid) Basic authentication credentials provided
                    by the Charge Point at the connection request.

Prerequisite(s)     The Central System supports security profile 1 and/or 2.

Before (Preparations)
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): The OCTT closes the connection.

Test Scenario
    1. The Charge Point sends a HTTP upgrade request without an Authorization header to the Central System.
    2. The Central System rejects the connection upgrade request.
       Note: The expected HTTP status code is not specified. Test assumes 401 Unauthorized.

    3. The Charge Point sends a HTTP upgrade request with an Authorization header, containing a
       username/password combination.
    4. The Central System validates the username/password combination AND accepts the connection upgrade request.

    5. The Charge Point sends a BootNotification.req
    6. The Central System responds with a BootNotification.conf
       Note: The expected BootNotification status is not specified. Test assumes Accepted.

    [Send per connector and connectorId=0.]
    7. The Charge Point sends a StatusNotification.req
    8. The Central System responds with a StatusNotification.conf

Tool Validations
    Note: The BasicAuthPassword that the tool will use to connect can be configured in two ways:
    1. When the configured value for BasicAuthPassword is >= 32 and <= 40 characters, the tool will expect that
       this is the hex encoded representation of the password.
    2. When the configured value for BasicAuthPassword is >= 16 and <= 20 characters, the tool will expect that
       this is plaintext (UTF-8) representation of the password.

    Post scenario validations: N/a

Expected result(s) / behaviour: Not explicitly listed in the CSMS document for this test case.
"""

import asyncio
import os
import pytest
import websockets
from websockets import InvalidStatusCode

from ocpp.v16.enums import RegistrationStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ADDRESS = os.environ['CSMS_ADDRESS']


@pytest.mark.asyncio
async def test_tc_085_no_auth_rejected():
    """Step 1-2: Connection without Authorization header is rejected."""
    with pytest.raises(InvalidStatusCode) as exc:
        await websockets.connect(
            uri=f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}',
            subprotocols=['ocpp1.6'],
            extra_headers={},
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_085(connection):
    """Step 3-8: Connection with valid auth succeeds, BootNotification + StatusNotification."""
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 5-6: BootNotification
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 7-8: StatusNotification per connector (connectorId=0 and connectorId=1)
    for cid in (0, 1):
        await cp.send_status_notification(cid)

    start_task.cancel()
