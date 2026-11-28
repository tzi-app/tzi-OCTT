"""
Test case name      Remote start transaction - Remote start first - Cable plugin timeout
Test case Id        TC_F_04_CSMS
Use case Id(s)      F02, E03
Requirement(s)      E03.FR.04, E03.FR.05

Requirement Details:
    E03.FR.04: (not found in OCPP 2.1 Part 2)
    E03.FR.05: The Charging Station SHOULD end the transaction and send a TransactionEventRequest (eventType =
               Ended, stoppedReason = Timeout, triggerReason = EVConnectionTimeout) to the CSMS.
        Precondition: When the EV Driver does not plug-in the charging cable before the timeout set by the
                      Configuration Variable: EVConnectionTimeOut AND TxStopPoint does not contain
                      ParkingBayOccupancy
        Note: This requirement is an additional safety measure to make sure the transaction is ended when the
              EVConnectionTimeOut is triggered. However it is up to the CSMS to make sure that sensible
              TxStartPoint / TxStopPoint combinations are configured. E.g. if Authorized is used as
              TxStartPoint, it should also be used as TxStopPoint.
System under test   CSMS

Description         OCPP 2.x.x allows an EV driver to either first wait for/trigger a
                    RequestStartTransactionRequest OR connect the EV and EVSE. Both sequences will result in
                    being able to charge.

Purpose             To verify if the CSMS is able to handle a Charging Station that deauthorizes the
                    transaction after the EVConnectionTimeout has been reached.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to request the Charging Station to start a transaction.

1. The CSMS sends a RequestStartTransactionRequest
2. The Test System responds with a RequestStartTransactionResponse
    - with status Accepted
    - transactionId is omitted.
3. The Test System sends a TransactionEventRequest.
    - with triggerReason is RemoteStart
    - transactionInfo.remoteStartId is <By Test System generated remoteStartID>
    - eventType is Started
4. The CSMS responds with a TransactionEventResponse.
5. The Test System sends a TransactionEventRequest.
    - with triggerReason is EVConnectTimeout
    - eventType is Updated
    Note(s):
    - This step will be executed after the _<Configured Transaction Duration> has been reached._
6. The CSMS responds with a TransactionEventResponse.

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
        (Part 2 errata - applies to this test via use case F02)
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
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_f_04(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger the CSMS to request the Charging Station to start a transaction.
    # 1. The CSMS sends a RequestStartTransactionRequest
    # 2. The Test System responds with a RequestStartTransactionResponse
    #    - with status Accepted
    #    - transactionId is omitted.
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
    #    - transactionInfo.remoteStartId is the remoteStartId of the RequestStartTransactionRequest
    #    - eventType is Started
    #    It has the idToken of the RequestStartTransactionRequest (F02.FR.05, F02.FR.12).
    # 4. The CSMS responds with a TransactionEventResponse.
    transaction_id = cp.session.start_transaction()
    await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='RemoteStart',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'remote_start_id': request.remote_start_id},
        id_token=request.id_token,
    ))

    # 5. The Test System sends a TransactionEventRequest.
    #    - with triggerReason is EVConnectTimeout
    #    - eventType is Updated
    #    Note(s): This step will be executed after the <Configured Transaction Duration> has
    #    been reached.
    # 6. The CSMS responds with a TransactionEventResponse.
    await asyncio.sleep(TRANSACTION_DURATION)
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='EVConnectTimeout',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
    ))

    start_task.cancel()
