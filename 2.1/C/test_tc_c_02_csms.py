"""
Test case name      Local start transaction - Authorization Invalid/Unknown
Test case Id        TC_C_02_CSMS
Use case Id(s)      C01, C04, C06
Requirement(s)      C01.FR.07 OR C04.FR.01 OR C06.FR.04

Requirement Details:
    C01.FR.07: AuthorizeResponse SHALL include an authorization status value indicating acceptance or a reason
               for rejection.
        Note: See AuthorizationStatusEnumType for the possible reasons of rejection.
    C04.FR.01: The CSMS SHALL respond with an AuthorizeResponse message with status = Invalid.
        Precondition: When the CSMS receives an AuthorizeRequest with a keyCode that is not valid at this
                      Charging Station
    C06.FR.04: it SHALL respond with an AuthorizeResponse and SHALL include an authorization status value
               indicating acceptance or a reason for rejection.
        Precondition: If the CSMS receives an AuthorizeRequest.
System under test   CSMS

Description         When a Charging Station needs to charge an EV, it needs to authorize the EV Driver first
                    at the CSMS before the charging can be started or stopped.

Purpose             To verify whether the CSMS is able to report that an idToken is NOT valid.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends an AuthorizeRequest
    with idToken.idToken <Configured invalid_idtoken_idtoken>
    idToken.type <Configured invalid_idtoken_type>
2. The CSMS responds with an AuthorizeResponse

Tool validations
* Step 2:
    Message: AuthorizeResponse
    - idTokenInfo.status Invalid or Unknown

Post scenario validations:
    - N/a
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
INVALID_ID_TOKEN = os.environ['INVALID_ID_TOKEN']
INVALID_ID_TOKEN_TYPE = os.environ['INVALID_ID_TOKEN_TYPE']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_02(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The Test System sends an AuthorizeRequest with
    #    idToken.idToken <Configured invalid_idtoken_idtoken>
    #    idToken.type <Configured invalid_idtoken_type>
    # 2. The CSMS responds with an AuthorizeResponse
    response = await cp.call(call.Authorize(
        id_token={'id_token': INVALID_ID_TOKEN, 'type': INVALID_ID_TOKEN_TYPE}))
    assert response.id_token_info.status in ('Invalid', 'Unknown'), \
        f"Expected AuthorizeResponse.idTokenInfo.status Invalid or Unknown, " \
        f"got {response.id_token_info.status}"

    start_task.cancel()
