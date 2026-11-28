"""
Test case name      Set Display Message - Specific transaction - Remove message after EndTime
Test case Id        TC_O_28_CSMS
Use case Id(s)      O02
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how the CSMS can be requested to send a SetDisplayMessageRequest
                    to the charging station. Depending on the given parameters the message shall be displayed
                    a certain way and at a certain moment on the Charging Station. These messages are
                    displayed additionally on a Charging Station and are not part of the firmware.

Purpose             To verify if the CSMS is able to send the request with an endTime for a specific
                    transaction according to the DisplayMessage mechanism as described in the OCPP
                    specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a SetDisplayMessageRequest
2. The Test System responds with a SetDisplayMessageResponse with status Accepted

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.state is <omitted>
    - message.startDateTime is <omitted>
    - message.endDateTime is <Configured endDateTime>
    - message.transactionId is <Generated transactionId from Before>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from display_messages import display_message, request_display_message
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_o_28(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # 1. The CSMS sends a SetDisplayMessageRequest
    # 2. The Test System responds with a SetDisplayMessageResponse with status Accepted
    end_date_time = utc_now_iso(600)
    request = await request_display_message(
        cp, display_message(transactionId=transaction_id, endDateTime=end_date_time))
    message = request.message
    assert message.state is None, f"message.state must be omitted, got {message.state}"
    assert message.start_date_time is None, \
        f"message.startDateTime must be omitted, got {message.start_date_time}"
    assert message.end_date_time == end_date_time, \
        f"Expected message.endDateTime {end_date_time}, got {message.end_date_time}"
    assert message.transaction_id == transaction_id, \
        f"Expected message.transactionId {transaction_id}, got {message.transaction_id}"

    start_task.cancel()
