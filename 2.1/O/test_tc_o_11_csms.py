"""
Test case name      Get a Specific Display Message - Unknown parameters
Test case Id        TC_O_11_CSMS
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

Prerequisite(s)     If the CSMS is able to send a GetDisplayMessage with an unknown id.

Configuration State N/a

Memory State        A display message is configured.

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetDisplayMessagesRequest
2. The Test System responds with a GetDisplayMessagesResponse with
    - status Unknown

Tool validations
* Step 1:
    Message GetDisplayMessagesRequest
    - id <A different generated Id>
    - requestId <Generated Id>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from display_messages import display_message_configured, MESSAGE_ID, request_display_messages
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_o_11(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: If the CSMS is able to send a GetDisplayMessage with an unknown id.
    # Memory State: A display message is configured.
    await display_message_configured(cp)

    # 1. The CSMS sends a GetDisplayMessagesRequest
    # 2. The Test System responds with a GetDisplayMessagesResponse with
    #    - status Unknown
    different_id = MESSAGE_ID + 1000
    request = await request_display_messages(cp, status='Unknown', id=[different_id])
    # id <A different generated Id>, requestId <Generated Id>
    assert request.id == [different_id], \
        f"Expected GetDisplayMessagesRequest.id [{different_id}], got {request.id}"
    assert request.request_id is not None, "GetDisplayMessagesRequest has no requestId"

    start_task.cancel()
