"""
Test case name      Trigger message - Heartbeat
Test case Id        TC_F_20_CSMS
Use case Id(s)      F06
Requirement(s)      F06.FR.01

Requirement Details:
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to trigger the Charging Station to send a HeartbeatRequest,
                    using a TriggerMessageRequest.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse with status Accepted
3. The Test System sends a HeartbeatRequest
4. The CSMS responds with a HeartbeatResponse

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage must be Heartbeat

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import trigger_message
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_f_20(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a TriggerMessageRequest
    # 2. The Test System responds with a TriggerMessageResponse with status Accepted
    cp.set_response('TriggerMessage', status='Accepted')
    request = await cp.wait_for_request(
        'TriggerMessage', manual_action=trigger_message(BASIC_AUTH_CP, 'Heartbeat'))
    assert request.requested_message == 'Heartbeat', \
        f"Expected TriggerMessageRequest.requestedMessage Heartbeat, got {request.requested_message}"

    # 3. The Test System sends a HeartbeatRequest
    # 4. The CSMS responds with a HeartbeatResponse
    await cp.send_heartbeat_request()

    start_task.cancel()
