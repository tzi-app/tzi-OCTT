"""
Test case name      Clear Monitoring - Too many elements
Test case Id        TC_N_18_CSMS
Use case Id(s)      N06
Requirement(s)      N06.FR.04

Requirement Details:
    N06.FR.04: The CSMS SHALL NOT put more id elements in a ClearVariableMonitoringRequest than reported by
               the Charging Station via: ItemsPerMessageClearVariableMonitoring and
               BytesPerMessageClearVariableMonitoring.
System under test   CSMS

Description         CSMS is requested to clear more monitors than allowed in one request.

Purpose             To test that CSMS does not exceed the ItemsPerMessageClearVariableMonitoring amount of
                    monitors in one request.

Prerequisite(s)     CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.

Configuration State This test requests the value of ItemsPerMessageClearVariableMonitoring and then instructs
                    the CSMS to clear (at least) one more monitor than allowed by this value. This value is
                    'read-only', so it cannot be manipulated in the test. As a consequence, if the Charging
                    Station supports more monitor ids in the list, than can be set by the CSMS, then this
                    cannot be tested.

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Instruct CSMS to send GetVariablesRequest with:
    - Component.name MonitoringCtrlr
    - Variable.name ItemsPerMessage
    - Variable.instance ClearVariableMonitoring.
2. The Test System responds with:
    GetVariablesResponse
3. Instruct CSMS to clear more monitors than allowed in ItemsPerMessage.
    ClearVariableMonitoringRequest with a list of ids
    Note: these monitor ids do not have to exist.
4. The Test System responds with:
    ClearVariableMonitoringResponse

Tool validations
* Step 1:
    Message: Two or more ClearVariableMonitoringRequest, so that the maximum number of
             ItemsPerMessageClearVariableMonitoring ids is never exceeded.
    Test System will reply with a ClearVariableMonitoringResponse for each ClearVariableMonitoringRequest, but
    the content of the responses is irrelevant for the test.

Post scenario validations:
    N/A
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from monitoring import (
    csms_requests_items_per_message,
    ITEMS_PER_MESSAGE_CLEAR_VARIABLE_MONITORING,
    MONITORING_VARIABLES,
)
from reusable_states.booted import booted
from trigger import clear_variable_monitoring
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_18(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisite: CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.
    cp.variables = dict(MONITORING_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Instruct CSMS to send GetVariablesRequest with:
    #    - Component.name MonitoringCtrlr
    #    - Variable.name ItemsPerMessage
    #    - Variable.instance ClearVariableMonitoring.
    # 2. The Test System responds with: GetVariablesResponse
    await csms_requests_items_per_message(cp)

    # 3. Instruct CSMS to clear more monitors than allowed in ItemsPerMessage.
    #    ClearVariableMonitoringRequest with a list of ids
    #    Note: these monitor ids do not have to exist.
    # 4. The Test System responds with: ClearVariableMonitoringResponse
    limit = ITEMS_PER_MESSAGE_CLEAR_VARIABLE_MONITORING
    monitor_ids = list(range(1, limit + 2))
    cp.forget_requests('ClearVariableMonitoring')
    before = len(cp.requests_of('ClearVariableMonitoring'))
    await clear_variable_monitoring(BASIC_AUTH_CP, monitor_ids)
    requests = cp.requests_of('ClearVariableMonitoring')[before:]

    # Two or more ClearVariableMonitoringRequest, so that the maximum number of
    # ItemsPerMessageClearVariableMonitoring ids is never exceeded.
    assert len(requests) >= 2, \
        f"Expected two or more ClearVariableMonitoringRequests for {len(monitor_ids)} ids with " \
        f"ItemsPerMessage {limit}, got {len(requests)}"
    for request in requests:
        assert len(request.id) <= limit, \
            f"A ClearVariableMonitoringRequest has {len(request.id)} ids, more than the {limit} of " \
            f"ItemsPerMessageClearVariableMonitoring: {request.id}"
    cleared = sorted(monitor_id for request in requests for monitor_id in request.id)
    assert cleared == monitor_ids, f"Expected the ids {monitor_ids} to be cleared, got {cleared}"

    start_task.cancel()
