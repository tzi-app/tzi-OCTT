"""
Test case name      Local start transaction - Authorization Expired
Test case Id        TC_C_07_CSMS
Use case Id(s)      C01
Requirement(s)      C01.FR.07

Requirement Details:
    C01.FR.07: AuthorizeResponse SHALL include an authorization status value indicating acceptance or a reason
               for rejection.
        Note: See AuthorizationStatusEnumType for the possible reasons of rejection.
System under test   CSMS

Description         When a Charging Station needs to charge an EV, it needs to authorize the EV Driver first
                    at the CSMS before the charging can be started or stopped.

Purpose             To verify whether the CSMS is able to report that an idToken is Expired.

Prerequisite(s)     N/a

Configuration State The IdToken configured as Expired at the Test System, must be set as Expired at the CSMS.

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured expired_idtoken_idtoken>
    - idToken.type <Configured expired_idtoken_type>
2. The CSMS responds with an AuthorizeResponse

Tool validations
* Step 2:
    Message: AuthorizeResponse
    - idTokenInfo.status Expired or Invalid

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EXPIRED_ID_TOKEN = os.environ['EXPIRED_ID_TOKEN']
EXPIRED_ID_TOKEN_TYPE = os.environ['EXPIRED_ID_TOKEN_TYPE']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_07(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The Test System sends an AuthorizeRequest with
    #    idToken.idToken <Configured expired_idtoken_idtoken>
    #    idToken.type <Configured expired_idtoken_type>
    # 2. The CSMS responds with an AuthorizeResponse
    response = await cp.call(call.Authorize(
        id_token={'id_token': EXPIRED_ID_TOKEN, 'type': EXPIRED_ID_TOKEN_TYPE}))
    assert response.id_token_info.status in ('Expired', 'Invalid'), \
        f"Expected AuthorizeResponse.idTokenInfo.status Expired or Invalid, " \
        f"got {response.id_token_info.status}"

    start_task.cancel()
