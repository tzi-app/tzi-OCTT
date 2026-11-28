"""
Test case name      Clear Monitoring - Rejected
Test case Id        TC_N_44_CSMS
Use case Id(s)      N06
Requirement(s)      N/a
System under test   CSMS

Description         A monitoring setting can be cleared (removed) by sending a ClearVariableMonitoringRequest
                    with the id of the monitoring setting.

Purpose             To verify if the CSMS is able to correctly read the respond from a charging station on a
                    request to clear a monitor that cannot be cleared as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a ClearVariableMonitoringRequest
2. The Test System responds with a ClearVariableMonitoringResponse with clearMonitoringResult[0].status
   Rejected

Tool validations
N/a

Post scenario validations:
    - N/a
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
async def test_tc_n_44(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a ClearVariableMonitoringRequest
    # 2. The Test System responds with a ClearVariableMonitoringResponse with
    #    clearMonitoringResult[0].status Rejected
    cp.set_response('ClearVariableMonitoring', lambda request: {'clear_monitoring_result': [
        {'status': 'Rejected', 'id': monitor_id} for monitor_id in request.id]})
    await cp.wait_for_request(
        'ClearVariableMonitoring',
        manual_action=send_call(BASIC_AUTH_CP, 'ClearVariableMonitoring', {'id': [1]}))

    start_task.cancel()
