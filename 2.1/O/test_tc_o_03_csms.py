"""
Test case name      Get all Display Messages - No DisplayMessages configured
Test case Id        TC_O_03_CSMS
Use case Id(s)      O03
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can request all the installed DisplayMessages
                    configured via OCPP in a Charging Station. The Charging Station can remove messages when
                    they are out-dated, or transactions have ended. It can be very useful for a CSO to be able
                    to view to current list of messages, so the CSO knows which messages are (still)
                    configured.

Purpose             To verify if the CSMS can request to get all display messages according to the
                    DisplayMessage mechanism as described in the OCPP specification when no messages are
                    configured.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetDisplayMessagesRequest
2. The Test System responds with a GetDisplayMessagesResponse with status Unknown

Tool validations
* Step 1:
    Message GetDisplayMessagesRequest
    - requestId <Generated request id>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from display_messages import request_display_messages
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_o_03(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a GetDisplayMessagesRequest
    # 2. The Test System responds with a GetDisplayMessagesResponse with status Unknown
    request = await request_display_messages(cp, status='Unknown')
    # requestId <Generated request id>
    assert request.request_id is not None, "GetDisplayMessagesRequest has no requestId"

    start_task.cancel()
