"""
Test case name      Trigger message - NotImplemented
Test case Id        TC_F_27_CSMS
Use case Id(s)      F06
Requirement(s)      F06.FR.08

Requirement Details:
    F06.FR.08: The Charging Station SHALL respond with TriggerMessageResponse with status NotImplemented.
        Precondition: When the Charging Station receives a TriggerMessageRequest with a requestedMessage that
                      it has not implemented
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to handle a Charging Station that does not support the
                    requested message value from a TriggerMessageRequest.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse with status NotImplemented

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
from trigger import trigger_message
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_f_27(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a TriggerMessageRequest
    #    It asks for a message that the Test System has not implemented.
    # 2. The Test System responds with a TriggerMessageResponse with status NotImplemented
    cp.set_response('TriggerMessage', status='NotImplemented')
    await cp.wait_for_request(
        'TriggerMessage',
        manual_action=trigger_message(BASIC_AUTH_CP, 'PublishFirmwareStatusNotification'))

    start_task.cancel()
