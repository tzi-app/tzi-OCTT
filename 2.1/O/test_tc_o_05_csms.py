"""
Test case name      Clear Display Message - Unknown Key
Test case Id        TC_O_05_CSMS
Use case Id(s)      O05
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can remove a specific message, configured via OCPP in a
                    Charging Station.

Purpose             To verify if the CSMS is able to request the Charging Station to clear a message according
                    to the mechanism as described in the OCPP specification.

Prerequisite(s)     If the CSMS supports sending a ClearDisplayMessageRequest with an unknown id.

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a ClearDisplayMessageRequest
2. The Test System responds with a ClearDisplayMessageResponse with status Unknown

Tool validations
N/a

Post scenario validations:
    - N/a
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

# The id of a display message that the Test System does not have
UNKNOWN_MESSAGE_ID = 987654


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_o_05(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: If the CSMS supports sending a ClearDisplayMessageRequest with an unknown id.
    # 1. The CSMS sends a ClearDisplayMessageRequest
    # 2. The Test System responds with a ClearDisplayMessageResponse with status Unknown
    cp.set_response('ClearDisplayMessage', status='Unknown')
    await cp.wait_for_request(
        'ClearDisplayMessage',
        manual_action=send_call(BASIC_AUTH_CP, 'ClearDisplayMessage', {'id': UNKNOWN_MESSAGE_ID}))

    start_task.cancel()
