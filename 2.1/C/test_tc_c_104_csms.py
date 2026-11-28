"""
Test case name      Authorization with prepaid card - no credit
Test case Id        TC_C_104_CSMS
Use case Id(s)      C17
Requirement(s)      C17.FR.02

Requirement Details:
    C17.FR.02: CSMS SHALL respond with an AuthorizeResponse with idTokenInfo that has status = NoCredit and
               cacheExpiryDateTime set to current date/time.
        Precondition: CSMS receives an AuthorizeRequest for an idToken that is valid and associated with a
                      prepaid account that does not have a positive balance
        Note: Prepaid token is not allowed to remain in the local authorization cache.
System under test   CSMS

Description         This test case verifies if the CSMS is able to authorize a prepaid card for a transaction.

Purpose             To verify if the CSMS is able to reject a prepaid card for a transaction.

Prerequisite(s)     - CSMS supports prepaid cards.
                    - Prepaid card with an amount of "0" is available.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a AuthorizeRequest with
    - idToken.idToken <prepaid card no credit id>
    - idToken.type = <prepaid card no credit id type>
2. The CSMS responds a AuthorizeResponse

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status NoCredit
    - idTokenInfo.cacheExpiryDateTime <current date/time>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import is_current_date_time, validate_id_token_info
from charge_point import TziChargePoint21
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
# Prerequisite: Prepaid card with an amount of "0" is available.
PREPAID_NO_CREDIT_ID_TOKEN = {'id_token': os.environ['PREPAID_NO_CREDIT_ID_TOKEN'],
                              'type': os.environ['PREPAID_NO_CREDIT_ID_TOKEN_TYPE']}


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_104(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The Test System sends a AuthorizeRequest with
    #    - idToken.idToken <prepaid card no credit id>
    #    - idToken.type = <prepaid card no credit id type>
    # 2. The CSMS responds a AuthorizeResponse
    response = await cp.call(call.Authorize(id_token=PREPAID_NO_CREDIT_ID_TOKEN))
    validate_id_token_info('AuthorizeResponse', response.id_token_info, status='NoCredit')
    # idTokenInfo.cacheExpiryDateTime <current date/time>
    cache_expiry = response.id_token_info.cache_expiry_date_time
    assert cache_expiry is not None, "AuthorizeResponse.idTokenInfo has no cacheExpiryDateTime"
    assert is_current_date_time(cache_expiry), \
        f"Expected AuthorizeResponse.idTokenInfo.cacheExpiryDateTime to be the current date/time, " \
        f"got {cache_expiry}"

    start_task.cancel()
