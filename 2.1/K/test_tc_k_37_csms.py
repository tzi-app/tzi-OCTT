"""
Test case name      Remote start transaction with charging profile - Success
Test case Id        TC_K_37_CSMS
Use case Id(s)      K05,F01
Requirement(s)      K05.FR.02, F01.FR.08, F01.FR.09, F01.FR.11

Requirement Details:
    K05.FR.02: The Purpose of the ChargingProfile SHALL always be TxProfile.
        Precondition: K05.FR.01
    F01.FR.08: The CSMS MAY include a ChargingProfile in the RequestStartTransactionRequest.
    F01.FR.09: The purpose of this ChargingProfile SHALL be set to TxProfile.
        Precondition: F01.FR.08
    F01.FR.11: The transactionId in the ChargingProfile SHALL NOT be set.
        Precondition: F01.FR.08
System under test   CSMS

Description         The CSMS sets a TxProfile on a specific EVSE inside a RequestStartTransactionRequest
                    message.

Purpose             To verify if the CSMS is able to set a TxProfile on a specific EVSE in a
                    RequestStartTransactionRequest message.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a RequestStartTransactionRequest
2. The Test System responds with a RequestStartTransactionResponse
    - With status Accepted
3. The Test System sends a TransactionEventRequest With
    - triggerReason RemoteStart
    - transactionInfo.remoteStartId is present.
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message: RequestStartTransactionRequest
    - idToken.idToken <Configured valid idToken>
    - idToken.type <Configured valid idToken type>
    - evseId <Configured evseId>
    - chargingProfile contains:
    - chargingProfile.chargingProfilePurpose is TxProfile
    - chargingProfile.transactionId is omitted
    - chargingProfile.chargingProfileKind is Relative OR Absolute
    - If chargingProfileKind is Relative then chargingSchedule.startSchedule must be omitted.
    - If chargingProfileKind is Absolute then chargingSchedule.startSchedule must NOT be omitted.

    The received Charging Profile must comply with the requirements defined at part 2 specification.

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
from smart_charging import (
    charging_profile,
    validate_part_2_requirements,
    validate_start_schedule_for_kind,
)
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
async def test_tc_k_37(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a RequestStartTransactionRequest
    # 2. The Test System responds with a RequestStartTransactionResponse
    #    - With status Accepted
    cp.set_response('RequestStartTransaction', status='Accepted')
    request = await cp.wait_for_request(
        'RequestStartTransaction',
        manual_action=send_call(BASIC_AUTH_CP, 'RequestStartTransaction', {
            'idToken': {'idToken': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
            'remoteStartId': 1,
            'evseId': CONFIGURED_EVSE_ID,
            'chargingProfile': charging_profile('TxProfile', 'Relative', 6, duration=False),
        }))
    assert request.id_token.id_token == VALID_ID_TOKEN, \
        f"Expected RequestStartTransactionRequest.idToken.idToken {VALID_ID_TOKEN}, " \
        f"got {request.id_token.id_token}"
    assert request.id_token.type == VALID_ID_TOKEN_TYPE, \
        f"Expected RequestStartTransactionRequest.idToken.type {VALID_ID_TOKEN_TYPE}, " \
        f"got {request.id_token.type}"
    assert request.evse_id == CONFIGURED_EVSE_ID, \
        f"Expected RequestStartTransactionRequest.evseId {CONFIGURED_EVSE_ID}, got {request.evse_id}"
    profile = request.charging_profile
    assert profile is not None, "RequestStartTransactionRequest has no chargingProfile"
    assert profile.charging_profile_purpose == 'TxProfile', \
        f"Expected chargingProfile.chargingProfilePurpose TxProfile, got {profile.charging_profile_purpose}"
    assert profile.transaction_id is None, \
        f"chargingProfile.transactionId must be omitted, got {profile.transaction_id}"
    assert profile.charging_profile_kind in ('Relative', 'Absolute'), \
        f"Expected chargingProfile.chargingProfileKind Relative or Absolute, " \
        f"got {profile.charging_profile_kind}"
    # If chargingProfileKind is Relative then chargingSchedule.startSchedule must be omitted. If
    # it is Absolute then it must NOT be omitted.
    validate_start_schedule_for_kind(profile)
    # The received Charging Profile must comply with the requirements defined at part 2
    # specification.
    validate_part_2_requirements(profile, evse_id=request.evse_id, in_request_start_transaction=True)

    # 3. The Test System sends a TransactionEventRequest With
    #    - triggerReason RemoteStart
    #    - transactionInfo.remoteStartId is present.
    #    It has the idToken of the RequestStartTransactionRequest (F02.FR.05, F02.FR.12).
    # 4. The CSMS responds with a TransactionEventResponse
    transaction_id = cp.session.start_transaction()
    await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='RemoteStart',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'remote_start_id': request.remote_start_id},
        id_token=request.id_token,
    ))

    start_task.cancel()
