"""
Test case name      Trigger message - CustomTrigger
Test case Id        TC_F_100_CSMS
Use case Id(s)      F06
Requirement(s)      …
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to trigger messages using a CustomTrigger.

Prerequisite(s)     The Test System reports support for the following:
                    component.name CustomizationCtrlr
                    variable.name CustomTriggers
                    variableAttribute.value [Custom1, Custom2, Custom3]

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Use CSMS to trigger custom trigger Custom2 for <Configured evseId>

1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse with
    - status Accepted

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage CustomTrigger
    - customTrigger Custom2
    - evse.id <Configured evseId>

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
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_f_100(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisite: The Test System reports support for the following: component.name
    # CustomizationCtrlr, variable.name CustomTriggers, variableAttribute.value [Custom1,
    # Custom2, Custom3]
    cp.variables = {'CustomizationCtrlr.CustomTriggers': 'Custom1,Custom2,Custom3'}
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Use CSMS to trigger custom trigger Custom2 for <Configured evseId>
    # 1. The CSMS sends a TriggerMessageRequest
    # 2. The Test System responds with a TriggerMessageResponse with
    #    - status Accepted
    cp.set_response('TriggerMessage', status='Accepted')
    request = await cp.wait_for_request(
        'TriggerMessage',
        manual_action=trigger_message(BASIC_AUTH_CP, 'CustomTrigger', evse_id=CONFIGURED_EVSE_ID,
                                      custom_trigger='Custom2'))
    assert request.requested_message == 'CustomTrigger', \
        f"Expected TriggerMessageRequest.requestedMessage CustomTrigger, " \
        f"got {request.requested_message}"
    assert request.custom_trigger == 'Custom2', \
        f"Expected TriggerMessageRequest.customTrigger Custom2, got {request.custom_trigger}"
    assert request.evse is not None and request.evse.id == CONFIGURED_EVSE_ID, \
        f"Expected TriggerMessageRequest.evse.id {CONFIGURED_EVSE_ID}, got {request.evse}"

    start_task.cancel()
