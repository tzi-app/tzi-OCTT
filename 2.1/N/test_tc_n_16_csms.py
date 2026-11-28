"""
Test case name      Set Monitoring Level - Success
Test case Id        TC_N_16_CSMS
Use case Id(s)      N05
Requirement(s)      N05.FR.01

Requirement Details:
    N05.FR.01: The Charging Station SHALL send a setMonitoringLevelResponse with Accepted.
        Precondition: When the Charging Station accepts a setMonitoringLevelRequest
System under test   CSMS

Description         CSMS sets a monitoring level.

Purpose             To test that CSMS supports setting of a monitoring level.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Instruct CSMS to set a monitoring level with severity = _4
2. Test System responds with:
    SetMonitoringLevelResponse with
    - Status is Accepted

Tool validations
* Step 1:
    Message: SetMonitoringLevelRequest with:
    - severity = 4

Post scenario validations:
    N/A
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


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_16(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Instruct CSMS to set a monitoring level with severity = 4
    # 2. Test System responds with: SetMonitoringLevelResponse with
    #    - Status is Accepted
    cp.set_response('SetMonitoringLevel', status='Accepted')
    request = await cp.wait_for_request(
        'SetMonitoringLevel',
        manual_action=send_call(BASIC_AUTH_CP, 'SetMonitoringLevel', {'severity': 4}))
    assert request.severity == 4, f"Expected SetMonitoringLevelRequest.severity 4, got {request.severity}"

    start_task.cancel()
