"""
Test case name      Battery Swap - Remote Start - not enough batteries
Test case Id        TC_S_102_CSMS
Use case Id(s)      S01
Requirement(s)      N/a
System under test   CSMS

Description         CSMS is able to support battery swapping.

Purpose             To verify whether the CSMS is able successful support battery swapping with not enough
                    batteries.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Let CSMS trigger a request for swapping batteries

1. The CSMS sends a RequestBatterySwapRequest
2. The Test System responds with a RequestBatterySwapResponse with
    - status Rejected
    - statusInfo.reasonCode NoBatteryAvailable

Tool validations
* Step 1:
    Message: RequestBatterySwapRequest
    - requestId must be <not omitted>
    - idToken.idToken must be <Configured valid_idtoken_idtoken>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_s_102(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Let CSMS trigger a request for swapping batteries
    # 1. The CSMS sends a RequestBatterySwapRequest
    # 2. The Test System responds with a RequestBatterySwapResponse with
    #    - status Rejected
    #    - statusInfo.reasonCode NoBatteryAvailable
    cp.set_response('RequestBatterySwap', status='Rejected',
                    status_info={'reason_code': 'NoBatteryAvailable'})
    request = await cp.wait_for_request(
        'RequestBatterySwap',
        manual_action=send_call(BASIC_AUTH_CP, 'RequestBatterySwap', {
            'idToken': {'idToken': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
            'requestId': 1,
        }))
    assert request.request_id is not None, "RequestBatterySwapRequest.requestId must not be omitted"
    assert request.id_token.id_token == VALID_ID_TOKEN, \
        f"Expected RequestBatterySwapRequest.idToken.idToken {VALID_ID_TOKEN}, " \
        f"got {request.id_token.id_token}"

    start_task.cancel()
