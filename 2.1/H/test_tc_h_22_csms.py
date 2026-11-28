"""
Test case name      Reserve a specific EVSE - Configured to Reject
Test case Id        TC_H_22_CSMS
Use case Id(s)      H01
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve a specific EVSE for a specific IdToken by sending a
                    ReserveNowRequest containing an evseId.

Purpose             To verify if the CSMS is able to correctly read the respond from a charging station when
                    it is configured not to accept reservations.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse with
    - status Rejected

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.reserved import reserve_now_payload
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_h_22(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a ReserveNowRequest
    # 2. The Test System responds with a ReserveNowResponse with
    #    - status Rejected
    cp.set_response('ReserveNow', status='Rejected')
    await cp.wait_for_request(
        'ReserveNow',
        manual_action=send_call(BASIC_AUTH_CP, 'ReserveNow', reserve_now_payload(
            evse_id=CONFIGURED_EVSE_ID)))

    start_task.cancel()
