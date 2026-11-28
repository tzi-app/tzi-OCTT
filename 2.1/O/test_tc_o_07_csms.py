"""
Test case name      Get a Specific Display Message - Id
Test case Id        TC_O_07_CSMS
Use case Id(s)      O04
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can request specific installed DisplayMessages
                    configured via OCPP in a Charging Station. The Charging Station can remove messages when
                    they are out-dated, or transactions have ended. It can be very useful for a CSO to be able
                    to view to current list of messages, so the CSO knows which messages are (still)
                    configured.

Purpose             To verify if the CSMS is able to request a specific id message from the charging station
                    according to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        A display message is configured.

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetDisplayMessagesRequest
2. The Test System responds with a GetDisplayMessagesResponse with status Accepted
3. The Test System sends a NotifyDisplayMessagesRequest
4. The CSMS responds with a NotifyDisplayMessagesResponse.

Tool validations
* Step 1:
    Message GetDisplayMessagesRequest
    - id <Configured_Id>
    - priority <Omitted>
    - state <Omitted>
    - requestId <Generated Id>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from display_messages import (
    display_message_configured,
    MESSAGE_ID,
    request_display_messages,
    validate_get_display_messages,
)
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_o_07(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Memory State: A display message is configured.
    message = await display_message_configured(cp)

    # 1. The CSMS sends a GetDisplayMessagesRequest
    # 2. The Test System responds with a GetDisplayMessagesResponse with status Accepted
    request = await request_display_messages(cp, id=[MESSAGE_ID])
    # id <Configured_Id>, priority <Omitted>, state <Omitted>, requestId <Generated Id>
    validate_get_display_messages(request, message_id=MESSAGE_ID)

    # 3. The Test System sends a NotifyDisplayMessagesRequest
    # 4. The CSMS responds with a NotifyDisplayMessagesResponse.
    await cp.send_notify_display_messages(request.request_id, message_info=[message])

    start_task.cancel()
