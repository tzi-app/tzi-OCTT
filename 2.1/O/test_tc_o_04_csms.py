"""
Test case name      Clear Display Message - Success
Test case Id        TC_O_04_CSMS
Use case Id(s)      O05
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can remove a specific message, configured via OCPP in a
                    Charging Station.

Purpose             To verify if the CSMS is able to request the Charging Station to clear a message according
                    to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        A display message is configured.

Reusable State      N/a

Test Scenario
Note: As a help method, a GetDisplayMessagesRequest is requested first for CSMS’s that implemented their
      ClearDisplayMessage as a combined feature.

1. The CSMS sends a ClearDisplayMessageRequest
2. The Test System responds with a ClearDisplayMessageResponse with status Accepted

Tool validations
* Step 1:
    Message ClearDisplayMessageRequest
    - id <Generated Id from set display message>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from display_messages import display_message_configured
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_o_04(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Memory State: A display message is configured.
    message = await display_message_configured(cp)

    # Note: As a help method, a GetDisplayMessagesRequest is requested first for CSMS's that
    #       implemented their ClearDisplayMessage as a combined feature.
    # 1. The CSMS sends a ClearDisplayMessageRequest
    # 2. The Test System responds with a ClearDisplayMessageResponse with status Accepted
    cp.set_response('ClearDisplayMessage', status='Accepted')
    request = await cp.wait_for_request(
        'ClearDisplayMessage',
        manual_action=send_call(BASIC_AUTH_CP, 'ClearDisplayMessage', {'id': message.id}))
    # id <Generated Id from set display message>
    assert request.id == message.id, \
        f"Expected ClearDisplayMessageRequest.id {message.id}, got {request.id}"

    start_task.cancel()
