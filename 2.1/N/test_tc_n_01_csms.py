"""
Test case name      Get Monitoring Report - with monitoringCriteria
Test case Id        TC_N_01_CSMS
Use case Id(s)      N02
Requirement(s)      N02.FR.05, N02.FR.10

Requirement Details:
    N02.FR.05: The set of monitors reported in one or more notifyMonitoringReportRequest messages is limited
               to the set defined by monitoringCriteria and componentVariables.
        Precondition: N02.FR.01 AND monitoringCriteria and componentVariables are NOT both absent.
    N02.FR.10: The Charging Station SHALL respond with a GetMonitoringReportResponse(status=EmptyResultSet).
        Precondition: When the Charging Station receives a GetMonitoringReportRequest with a combination of
                      criteria which results in an empty result set.
System under test   CSMS

Description         CSMS requests a report of monitors that match the component criteria.

Purpose             To test that CSMS supports requesting a monitoring report for the component criteria and
                    that it handles an empty result set.

Prerequisite(s)     CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.

Configuration State N/a

Memory State        CSMS requests ClearVariableMonitoring ItemsPerMessage from CS.

Reusable State(s)   N/a

Test Scenario
Manual Action: Manually instruct CSMS to get a report of monitors for:
- all DeltaMonitoring

1. CSMS sends GetMonitoringReportRequest
2. Test System responds with:
    GetMonitoringReportResponse with:
    - Status EmptyResultSet

Manual Action: Manually instruct CSMS to get a report of monitors for:
- all ThresholdMonitoring

3. CSMS sends GetMonitoringReportRequest
4. Test System responds with:
    GetMonitoringReportResponse with:
    - Status Accepted
5. Test System responds with:
    NotifyMonitoringReportRequest
6. CSMS sends NotifyMonitoringReportResponse

Step 5 and 6 are repeated as often as needed to report all configuration variables.

Tool validations
* Step 1:
    Message: GetMonitoringReportRequest
    - monitoringCriteria = DeltaMonitoring
    - componentVariable is omitted.
* Step 3:
    Message: GetMonitoringReportRequest
    - monitoringCriteria = ThresholdMonitoring
    - componentVariable is omitted.

Post scenario validations:
    Check that CSMS shows the Threshold monitors.
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from monitoring import (
    csms_requests_items_per_message,
    MONITORING_VARIABLES,
    request_monitoring_report,
    THRESHOLD_MONITORS,
    validate_monitoring_criteria,
)
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_01(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisite: CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.
    cp.variables = dict(MONITORING_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Memory State: CSMS requests ClearVariableMonitoring ItemsPerMessage from CS.
    await csms_requests_items_per_message(cp)

    # Manual Action: Manually instruct CSMS to get a report of monitors for:
    #     - all DeltaMonitoring
    # 1. CSMS sends GetMonitoringReportRequest
    # 2. Test System responds with: GetMonitoringReportResponse with:
    #    - Status EmptyResultSet
    request = await request_monitoring_report(
        cp, 'EmptyResultSet', monitoring_criteria=['DeltaMonitoring'], request_id=1)
    validate_monitoring_criteria(request, 'DeltaMonitoring')
    assert request.component_variable is None, \
        f"GetMonitoringReportRequest.componentVariable must be omitted, got {request.component_variable}"

    # Manual Action: Manually instruct CSMS to get a report of monitors for:
    #     - all ThresholdMonitoring
    # 3. CSMS sends GetMonitoringReportRequest
    # 4. Test System responds with: GetMonitoringReportResponse with:
    #    - Status Accepted
    request = await request_monitoring_report(
        cp, 'Accepted', monitoring_criteria=['ThresholdMonitoring'], request_id=2)
    validate_monitoring_criteria(request, 'ThresholdMonitoring')
    assert request.component_variable is None, \
        f"GetMonitoringReportRequest.componentVariable must be omitted, got {request.component_variable}"

    # 5. Test System responds with: NotifyMonitoringReportRequest
    # 6. CSMS sends NotifyMonitoringReportResponse
    # Step 5 and 6 are repeated as often as needed to report all configuration variables.
    await cp.send_notify_monitoring_report(request.request_id, seq_no=0, monitor=THRESHOLD_MONITORS)
    # "Check that CSMS shows the Threshold monitors" is a check in the CSMS itself.

    start_task.cancel()
