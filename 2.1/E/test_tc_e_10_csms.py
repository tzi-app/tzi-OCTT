"""
Test case name      Start transaction options - Authorized - Local
Test case Id        TC_E_10_CSMS
Use case Id(s)      E01(S3)
Requirement(s)      E01.FR.03

Requirement Details:
    E01.FR.03: The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType =
               Started) to the CSMS.
        Precondition: TxStartPoint contains: Authorized AND The EV Driver is authorized AND No transaction has
                      started yet
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the start options.

Purpose             To verify if the CSMS is able to handle a Charging Station that starts a transaction when
                    the EV and EVSE are connected.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends an AuthorizeRequest with:
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System sends a TransactionEventRequest with:
    - eventType is Started
    - triggerReason is Authorized
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: AuthorizeResponse
    - idTokenInfo.status must be Accepted
* Step 4:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_10(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    id_token = {'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE}

    # 1. The Test System sends an AuthorizeRequest with:
    #    - idToken.idToken <Configured valid_idtoken_idtoken>
    #    - idToken.type <Configured valid_idtoken_type>
    # 2. The CSMS responds with an AuthorizeResponse
    response = await cp.call(call.Authorize(id_token=id_token))
    validate_id_token_info('AuthorizeResponse', response.id_token_info, status='Accepted')

    # 3. The Test System sends a TransactionEventRequest with:
    #    - eventType is Started
    #    - triggerReason is Authorized
    #    - idToken.idToken <Configured valid_idtoken_idtoken>
    #    - idToken.type <Configured valid_idtoken_type>
    # 4. The CSMS responds with a TransactionEventResponse
    transaction_id = cp.session.start_transaction()
    response = await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='Authorized',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        id_token=id_token,
    ))
    validate_id_token_info('TransactionEventResponse', response.id_token_info, status='Accepted')

    start_task.cancel()
