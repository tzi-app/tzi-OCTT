"""
Test case name      Basic Authentication - Username does not equal ChargingStationId
Test case Id        TC_A_02_CSMS
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
1. The OCTT sends a HTTP upgrade request with an Authorization header, containing a username/password combination.
2. The CSMS validates the username/password combination AND rejects the connection upgrade request.
"""

import pytest
import os
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP201_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP + "wrong", TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_a_02(connection):
    assert connection.open == False
    assert connection.status_code == 401
