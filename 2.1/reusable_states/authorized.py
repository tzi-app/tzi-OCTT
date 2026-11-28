"""
State               Authorized
System under test   CSMS
Description         This state will simulate that the EV Driver is locally authorizing to start a transaction
                    on the simulated Charging Station.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

1. The Test System sends an AuthorizeRequest With idToken.idToken <Configured valid_idtoken_idtoken>
   idToken.type <Configured valid_idtoken_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System sends a TransactionEventRequest With triggerReason is Authorized
   idToken.idToken <Configured valid_idtoken_idtoken>
   idToken.type <Configured valid_idtoken_type>

If State is EVConnectedPreSession then
    eventType is Updated
else
    eventType is Started

4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2: Message: AuthorizeResponse - idTokenInfo.status must be Accepted
* Step 4: Message: TransactionEventResponse - idTokenInfo.status must be Accepted
Post condition      State is Authorized
"""

import os

from ocpp.v21 import call

from charge_point import ChargingSession, TziChargePoint21
from ocpp_messages import utc_now_iso

VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']


async def authorized(cp: TziChargePoint21, id_token: str = VALID_ID_TOKEN,
                     id_token_type: str = VALID_ID_TOKEN_TYPE, session: ChargingSession = None):
    """Returns the id of the transaction.

    session: the charging session this is about, when the scenario has more than one."""
    session = session or cp.session
    token = {'id_token': id_token, 'type': id_token_type}

    # 1. The Test System sends an AuthorizeRequest With idToken.idToken <Configured
    #    valid_idtoken_idtoken> idToken.type <Configured valid_idtoken_type>
    # 2. The CSMS responds with an AuthorizeResponse
    authorize_response = await cp.call(call.Authorize(id_token=token))
    assert authorize_response.id_token_info.status == 'Accepted', \
        f"Expected AuthorizeResponse.idTokenInfo.status Accepted, got {authorize_response.id_token_info.status}"

    # 3. The Test System sends a TransactionEventRequest With triggerReason is Authorized and
    #    the idToken. If State is EVConnectedPreSession then eventType is Updated, else
    #    eventType is Started.
    # 4. The CSMS responds with a TransactionEventResponse
    if session.transaction_id is None:
        event_type = 'Started'
        session.start_transaction()
    else:
        event_type = 'Updated'
    response = await cp.call(call.TransactionEvent(
        event_type=event_type,
        timestamp=utc_now_iso(),
        trigger_reason='Authorized',
        seq_no=session.next_seq_no(),
        transaction_info={'transaction_id': session.transaction_id},
        id_token=token,
    ))
    assert response.id_token_info is not None, \
        "TransactionEventResponse has no idTokenInfo, which is required when the request has an idToken"
    assert response.id_token_info.status == 'Accepted', \
        f"Expected TransactionEventResponse.idTokenInfo.status Accepted, got {response.id_token_info.status}"

    session.state = 'Authorized'
    session.authorized = True
    session.id_token = token
    return session.transaction_id
