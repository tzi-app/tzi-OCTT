"""
Test case name      Set Monitoring Level - Out of range
Test case Id        TC_N_17_CSMS
Use case Id(s)      N05
Requirement(s)      N05.FR.02

Requirement Details:
    N05.FR.02: The Charging Station SHALL send a setMonitoringLevelResponse with Rejected .
        Precondition: When the Charging Station receives a setMonitoringLevelRequest for a severity that is
                      out of range
System under test   CSMS

Description         CSMS sets a monitoring level.

Purpose             To test that CSMS supports the rejection of setting of a monitoring level.

Prerequisite(s)     The Test System will always reject the message, but normally this would only occur if the
                    set severity level is out of range.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Instruct CSMS to set a monitoring level with severity = 4
2. Test System responds with:
    SetMonitoringLevelResponse with
    - Status is Rejected

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
async def test_tc_n_17(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Instruct CSMS to set a monitoring level with severity = 4
    # 2. Test System responds with: SetMonitoringLevelResponse with
    #    - Status is Rejected
    cp.set_response('SetMonitoringLevel', status='Rejected')
    request = await cp.wait_for_request(
        'SetMonitoringLevel',
        manual_action=send_call(BASIC_AUTH_CP, 'SetMonitoringLevel', {'severity': 4}))
    assert request.severity == 4, f"Expected SetMonitoringLevelRequest.severity 4, got {request.severity}"

    start_task.cancel()
