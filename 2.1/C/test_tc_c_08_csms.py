"""
Test case name      Authorization through authorization cache - Accepted
Test case Id        TC_C_08_CSMS
Use case Id(s)      C12
Requirement(s)      C12_FR_03

Requirement Details:
    C12.FR.03: The CSMS SHALL check the authorization status of the IdToken when processing this
               TransactionEventRequest.
        Precondition: C12.FR.02
System under test   CSMS

Description         This test case describes how the EV Driver is authorized to start a transaction while the
                    Charging Station uses Cached IdToken. This enables the EV Driver to Online start a
                    transaction by using the Authorization Cache in which the Charging Station can respond
                    faster, as no AuthorizeRequest is being sent.

Purpose             To verify if the CSMS is able to respond correctly when an idToken which has status
                    "Accepted" in the charging stations cache is presented according to the mechanism as
                    described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      State is EVConnectedPreSession

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - triggerReason Authorized
    - idToken <Valid id token configured in Authorization Cache>
    - eventType Updated
    Note(s):
    - TxStartPoint contains ParkingBayOccupancy
2. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_08(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EVConnectedPreSession
    transaction_id = await ev_connected_pre_session(cp)

    # 1. The Test System sends a TransactionEventRequest with
    #    - triggerReason Authorized
    #    - idToken <Valid id token configured in Authorization Cache>
    #    - eventType Updated
    #    The idToken is in the station's Authorization Cache, so no AuthorizeRequest is sent.
    # 2. The CSMS responds with a TransactionEventResponse
    response = await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='Authorized',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        id_token={'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
    ))
    assert response.id_token_info is not None, "TransactionEventResponse has no idTokenInfo"
    assert response.id_token_info.status == 'Accepted', \
        f"Expected TransactionEventResponse.idTokenInfo.status Accepted, got {response.id_token_info.status}"

    start_task.cancel()
