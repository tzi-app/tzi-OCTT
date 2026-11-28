"""
Test case name      Authorization by GroupId - Success
Test case Id        TC_C_39_CSMS
Use case Id(s)      C09
Requirement(s)      C09_FR_02, C09_FR_03

Requirement Details:
    C09.FR.02: IdTokens that are part of the same group for authorization purposes SHALL have a common group
               identifier in the optional groupIdToken element in IdTokenInfo
    C09.FR.03: An EV Driver with a different, valid IdToken, but with the same groupIdToken SHALL be
               authorized to stop the transaction.
        Precondition: When a transaction has been authorized/started with a certain IdToken.
System under test   CSMS

Description         This test case covers how a Charging Station can authorize an action for an EV Driver
                    based on GroupId information. This could for example be used if 2 people regularly use the
                    same EV: they can use their own IdToken (e.g. RFID card), and can deauthorize transactions
                    that were started with the other idToken (with the same GroupId).

Purpose             To verify if the CSMS is able to correctly handle the Authorization of idTokens with the
                    same GroupId according to the mechanism as described in the OCPP specification.

Prerequisite(s)     - N/a

Configuration State N/a

Memory State        Two valid idTokens with the same GroupId are configured

Reusable State(s)   state is EVConnectedPreSession

Test Scenario
1. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured valid_idtoken2_idtoken>
    - idToken.type <Configured valid_idtoken2_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System sends a TransactionEventRequest with
    - triggerReason Authorized
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type> if transaction was already started
    - eventType Updated
    else
    - eventType Started
4. The CSMS responds with a TransactionEventResponse
5. Execute Reusable State EnergyTransferStarted
6. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured valid_idtoken2_idtoken>
    - idToken.type <Configured valid_idtoken2_type>
7. The CSMS responds with an AuthorizeResponse
8. The Test System sends a TransactionEventRequest with
    - triggerReason StopAuthorized
    - idToken.idToken <Configured valid_idtoken2_idtoken>
    - idToken.type <Configured valid_idtoken2_type>
    - eventType Updated
9. The CSMS responds with a TransactionEventResponse
10. Execute Reusable State EVConnectedPostSession
11. Execute Reusable State EVDisconnected

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
* Step 4:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
* Step 7:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
* Step 9:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_connected_post_session import ev_connected_post_session
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from reusable_states.ev_disconnected import ev_disconnected
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
# Memory State: Two valid idTokens with the same GroupId are configured
VALID_ID_TOKEN = {'id_token': os.environ['VALID_ID_TOKEN'], 'type': os.environ['VALID_ID_TOKEN_TYPE']}
VALID_ID_TOKEN_2 = {'id_token': os.environ['VALID_ID_TOKEN_2'], 'type': os.environ['VALID_ID_TOKEN_TYPE_2']}
GROUP_ID = os.environ['GROUP_ID']


def _validate_id_token_info(message, id_token_info):
    # idTokenInfo.status Accepted, idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
    validate_id_token_info(message, id_token_info, status='Accepted', group_id=GROUP_ID)


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_39(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: state is EVConnectedPreSession
    transaction_id = await ev_connected_pre_session(cp)

    # 1. The Test System sends an AuthorizeRequest with
    #    - idToken.idToken <Configured valid_idtoken2_idtoken>
    #    - idToken.type <Configured valid_idtoken2_type>
    # 2. The CSMS responds with an AuthorizeResponse
    response = await cp.call(call.Authorize(id_token=VALID_ID_TOKEN_2))
    _validate_id_token_info('AuthorizeResponse', response.id_token_info)

    # 3. The Test System sends a TransactionEventRequest with
    #    - triggerReason Authorized
    #    - idToken.idToken <Configured valid_idtoken_idtoken>
    #    - idToken.type <Configured valid_idtoken_type>
    #    - eventType Updated, because the transaction was already started
    # 4. The CSMS responds with a TransactionEventResponse
    response = await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='Authorized',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        id_token=VALID_ID_TOKEN,
    ))
    _validate_id_token_info('TransactionEventResponse', response.id_token_info)
    cp.session.state = 'Authorized'
    cp.session.authorized = True
    cp.session.id_token = VALID_ID_TOKEN

    # 5. Execute Reusable State EnergyTransferStarted
    await energy_transfer_started(cp)

    # 6. The Test System sends an AuthorizeRequest with
    #    - idToken.idToken <Configured valid_idtoken2_idtoken>
    #    - idToken.type <Configured valid_idtoken2_type>
    # 7. The CSMS responds with an AuthorizeResponse
    response = await cp.call(call.Authorize(id_token=VALID_ID_TOKEN_2))
    _validate_id_token_info('AuthorizeResponse', response.id_token_info)

    # 8. The Test System sends a TransactionEventRequest with
    #    - triggerReason StopAuthorized
    #    - idToken.idToken <Configured valid_idtoken2_idtoken>
    #    - idToken.type <Configured valid_idtoken2_type>
    #    - eventType Updated
    # 9. The CSMS responds with a TransactionEventResponse
    response = await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='StopAuthorized',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        id_token=VALID_ID_TOKEN_2,
    ))
    _validate_id_token_info('TransactionEventResponse', response.id_token_info)
    cp.session.state = 'StopAuthorized'
    cp.session.authorized = False

    # 10. Execute Reusable State EVConnectedPostSession
    await ev_connected_post_session(cp)

    # 11. Execute Reusable State EVDisconnected
    await ev_disconnected(cp)

    start_task.cancel()
