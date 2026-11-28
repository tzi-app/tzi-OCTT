"""
Test case name      Set Display Message - Display message at StartTime
Test case Id        TC_O_13_CSMS
Use case Id(s)      O01
Requirement(s)      O01_FR_05

Requirement Details:
    O01.FR.05: The CSMS MAY include a startTime and endTime when setting a message.
System under test   CSMS

Description         This test case describes how the CSMS can be requested to sent an SetDisplayMessageRequest
                    to the charging station. Depending on the given parameters the message shall be displayed
                    a certain way and at a certain moment on the Charging Station. These messages are
                    displayed additionally on a Charging Station and are not part of the firmware.

Purpose             To verify if the CSMS is able to send the request with a startTime according to the
                    DisplayMessage mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to send a SetDisplayMessageRequest with a startTime.

1. The CSMS sends a SetDisplayMessageRequest
2. The Test System responds with a SetDisplayMessageResponse with status Accepted

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.id <Generated Id>
    - message.startDateTime <Configured startDateTime>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from display_messages import display_message, request_display_message, validate_message
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_o_13(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to send a SetDisplayMessageRequest with a startTime.
    # 1. The CSMS sends a SetDisplayMessageRequest
    # 2. The Test System responds with a SetDisplayMessageResponse with status Accepted
    start_date_time = utc_now_iso(60)
    request = await request_display_message(cp, display_message(startDateTime=start_date_time))
    # message.id <Generated Id>, message.startDateTime <Configured startDateTime>
    validate_message(request, priority=None)
    assert request.message.start_date_time == start_date_time, \
        f"Expected SetDisplayMessageRequest.message.startDateTime {start_date_time}, " \
        f"got {request.message.start_date_time}"

    start_task.cancel()
