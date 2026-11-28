"""
Test case name      Authorization with prepaid card - success
Test case Id        TC_C_103_CSMS
Use case Id(s)      C17
Requirement(s)      C17.FR.01, C17.FR.03

Requirement Details:
    C17.FR.01: CSMS SHALL respond with an AuthorizeResponse with idTokenInfo with status = Accepted and
               cacheExpiryDateTime set to current date/time.
        Precondition: CSMS receives an AuthorizeRequest for an idToken that is valid and associated with a
                      prepaid account that has a positive balance
        Note: Prepaid token is not allowed to remain in the local authorization cache.
    C17.FR.03: CSMS SHALL include (only one time) the field transactionLimit.maxCost, set to the maximum
               amount that may be spent, in the TransactionEventResponse
        Precondition: CSMS receives an TransactionEventRequest with an idToken that is valid and associated
                      with a prepaid account that has a positive balance
        Note: See also E16 - Transactions with fixed cost, energy, SoC or time.
System under test   CSMS

Description         This test case verifies if the CSMS is able to authorize a prepaid card for a transaction.

Purpose             To verify if the CSMS is able to authorize a prepaid card for a transaction.

Prerequisite(s)     - CSMS supports prepaid cards.
                    - Prepaid card with positive amount is available.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a AuthorizeRequest with
    - idToken.idToken <prepaid card id>
    - idToken.type = <prepaid card id type>
2. The CSMS responds a AuthorizeResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Started
    - idToken.idToken <prepaid card id>
    - idToken.type = <prepaid card id type>
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.cacheExpiryDateTime <current date/time>
* Step 4:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.cacheExpiryDateTime <cacheExpiryDateTime from step 2>
    - transactionLimit.maxCost = <not omitted>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import is_current_date_time, validate_id_token_info
from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
# Prerequisite: Prepaid card with positive amount is available.
PREPAID_ID_TOKEN = {'id_token': os.environ['PREPAID_ID_TOKEN'], 'type': os.environ['PREPAID_ID_TOKEN_TYPE']}


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_103(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The Test System sends a AuthorizeRequest with
    #    - idToken.idToken <prepaid card id>
    #    - idToken.type = <prepaid card id type>
    # 2. The CSMS responds a AuthorizeResponse
    response = await cp.call(call.Authorize(id_token=PREPAID_ID_TOKEN))
    validate_id_token_info('AuthorizeResponse', response.id_token_info, status='Accepted')
    # idTokenInfo.cacheExpiryDateTime <current date/time>
    authorize_cache_expiry = response.id_token_info.cache_expiry_date_time
    assert authorize_cache_expiry is not None, "AuthorizeResponse.idTokenInfo has no cacheExpiryDateTime"
    assert is_current_date_time(authorize_cache_expiry), \
        f"Expected AuthorizeResponse.idTokenInfo.cacheExpiryDateTime to be the current date/time, " \
        f"got {authorize_cache_expiry}"

    # 3. The Test System sends a TransactionEventRequest with
    #    - eventType Started
    #    - idToken.idToken <prepaid card id>
    #    - idToken.type = <prepaid card id type>
    # 4. The CSMS responds with a TransactionEventResponse
    transaction_id = cp.session.start_transaction()
    response = await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='Authorized',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        id_token=PREPAID_ID_TOKEN,
    ))
    validate_id_token_info('TransactionEventResponse', response.id_token_info, status='Accepted')
    # idTokenInfo.cacheExpiryDateTime <cacheExpiryDateTime from step 2>: the one of step 2, or
    # the current date/time again, as in the sequence diagram of C17. Either way the prepaid
    # token does not remain in the authorization cache.
    cache_expiry = response.id_token_info.cache_expiry_date_time
    assert cache_expiry is not None, "TransactionEventResponse.idTokenInfo has no cacheExpiryDateTime"
    assert cache_expiry == authorize_cache_expiry or is_current_date_time(cache_expiry), \
        f"Expected TransactionEventResponse.idTokenInfo.cacheExpiryDateTime {authorize_cache_expiry} " \
        f"(the one of the AuthorizeResponse), got {cache_expiry}"
    # transactionLimit.maxCost = <not omitted>
    assert response.transaction_limit is not None and response.transaction_limit.max_cost is not None, \
        f"TransactionEventResponse has no transactionLimit.maxCost: {response.transaction_limit}"

    start_task.cancel()
