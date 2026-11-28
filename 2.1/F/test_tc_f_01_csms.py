"""
Test case name      Remote start transaction - Cable plugin first
Test case Id        TC_F_01_CSMS
Use case Id(s)      F01
Requirement(s)      N/a
System under test   CSMS

Description         OCPP 2.x.x allows an EV driver to either first connect the EV and EVSE OR wait for/trigger
                    a RequestStartTransactionRequest. Both sequences will result in being able to charge.

Purpose             To verify if the CSMS is able to handle a Charging Station that is starts a charging
                    session when the EV driver first connects the EV and EVSE, before receiving a
                    RequestStartTransactionRequest message.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession

Test Scenario
Manual Action: Trigger the CSMS to request the Charging Station to start a transaction.

1. The CSMS sends a RequestStartTransactionRequest
2. The Test System responds with a RequestStartTransactionResponse
    - with status Accepted
    - transactionId is <Generated transactionId>
3. The Test System sends a TransactionEventRequest.
    - with triggerReason is RemoteStart
    - transactionInfo.remoteStartId is <By CSMS provided remoteStartID>
    - eventType is Updated
4. The CSMS responds with a TransactionEventResponse.
5. Execute Reusable State EnergyTransferStarted (State is Authorized and _EVConnected = true)

Tool validations
* Step 1:
    Message: RequestStartTransactionRequest
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.13. Page 227 - (2026-06) - New F01.FR.27 and F02.FR.28 for evseId in RequestStartTransactionRequest
        [1281]
        (Part 2 errata - applies to this test via use case F01)
        There has always been an implicit (silent) requirement that a CSMS is able to provide an EVSE ID in a
        RequestStartTransactionRequest. It is only for flexibility that the option was given to let the
        charging station decide which EVSE to use if it is able to do so. A charging station that cannot do
        this can reject the request. In that case CSMS will have to send a new RequestStartTransaction with an
        EVSE ID.

        Unfortunately, due to the evseId being an optional field, a CSMS could be implemented that is never
        sending an evseId and still comply to the requirements. Therefore, a new requirement is added to close
        this gap.

        New requirement

        | ID | Precondition | Requirement definition | Note |
        | F01.FR.27 |  | CSMS SHALL be able to provide an evseId in a RequestStartTransactionRequest for
          interoperability with Charging Stations that do not accept RequestStartTransactionRequest without
          it. | F01.FR.07 allows a charging station to reject a request without evseId. F01.FR.06 allows CSMS
          to send a request without evseId, but in case of F01.FR.07 it must be able to provide a evseId. |

        The same requirement is also for F02.

        New requirement

        | ID | Precondition | Requirement definition | Note |
        | F02.FR.28 |  | CSMS SHALL be able to provide an evseId in a RequestStartTransactionRequest for
          interoperability with Charging Stations that do not accept RequestStartTransactionRequest without
          it. | (Same as F01.FR.27) / F02.FR.15 allows a charging station to reject a request without evseId.
          F02.FR.14 allows CSMS to send a request without evseId, but in case of F02.FR.15 it must be able to
          provide a evseId. |
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_f_01(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EVConnectedPreSession
    transaction_id = await ev_connected_pre_session(cp)

    # Manual Action: Trigger the CSMS to request the Charging Station to start a transaction.
    # 1. The CSMS sends a RequestStartTransactionRequest
    # 2. The Test System responds with a RequestStartTransactionResponse
    #    - with status Accepted
    #    - transactionId is <Generated transactionId>
    cp.set_response('RequestStartTransaction', status='Accepted', transaction_id=transaction_id)
    request = await cp.wait_for_request(
        'RequestStartTransaction',
        manual_action=send_call(BASIC_AUTH_CP, 'RequestStartTransaction', {
            'idToken': {'idToken': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
            'remoteStartId': 1,
            'evseId': CONFIGURED_EVSE_ID,
        }))
    assert request.id_token.id_token == VALID_ID_TOKEN, \
        f"Expected RequestStartTransactionRequest.idToken.idToken {VALID_ID_TOKEN}, " \
        f"got {request.id_token.id_token}"
    assert request.id_token.type == VALID_ID_TOKEN_TYPE, \
        f"Expected RequestStartTransactionRequest.idToken.type {VALID_ID_TOKEN_TYPE}, " \
        f"got {request.id_token.type}"

    # 3. The Test System sends a TransactionEventRequest.
    #    - with triggerReason is RemoteStart
    #    - transactionInfo.remoteStartId is <By CSMS provided remoteStartID>
    #    - eventType is Updated
    #    It has the idToken of the RequestStartTransactionRequest (F01.FR.04).
    # 4. The CSMS responds with a TransactionEventResponse.
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='RemoteStart',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'remote_start_id': request.remote_start_id},
        id_token=request.id_token,
    ))
    cp.session.state = 'Authorized'
    cp.session.authorized = True
    cp.session.id_token = request.id_token

    # 5. Execute Reusable State EnergyTransferStarted (State is Authorized and EVConnected = true)
    await energy_transfer_started(cp)

    start_task.cancel()
