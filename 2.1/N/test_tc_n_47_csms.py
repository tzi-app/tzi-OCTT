"""
Test case name      Get Monitoring report - Report all
Test case Id        TC_N_47_CSMS
Use case Id(s)      N02
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how the CSMS requests the Charging Station to send a report about
                    configured monitoring settings per component and variable. Optionally, this list can be
                    filtered on monitoringCriteria and componentVariables.

Purpose             To verify if the CSMS is able to send a get monitor request omitting the
                    monitoringCriteria and componentVariable as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetMonitoringReportRequest
2. The Test System responds with a GetMonitoringReportResponse
3. The Test System sends a NotifyMonitoringReportRequest
4. The CSMS responds with a NotifyMonitoringReportResponse.

Note(s):
- If tbc is True at Step 3 then step 3 and 4 will be repeated

Tool validations
* Step 1:
    Message GetMonitoringReportRequest
    - monitoringCriteria omitted AND
    - componentVariable omitted.

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from monitoring import (
    DELTA_MONITORS,
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
async def test_tc_n_47(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a GetMonitoringReportRequest
    # 2. The Test System responds with a GetMonitoringReportResponse
    request = await request_monitoring_report(cp, 'Accepted')
    # monitoringCriteria omitted AND componentVariable omitted.
    validate_monitoring_criteria(request)
    assert request.component_variable is None, \
        f"GetMonitoringReportRequest.componentVariable must be omitted, got {request.component_variable}"

    # 3. The Test System sends a NotifyMonitoringReportRequest
    # 4. The CSMS responds with a NotifyMonitoringReportResponse.
    # Note(s): If tbc is True at Step 3 then step 3 and 4 will be repeated
    await cp.send_notify_monitoring_report(
        request.request_id, seq_no=0, monitor=DELTA_MONITORS, tbc=True)
    await cp.send_notify_monitoring_report(
        request.request_id, seq_no=1, monitor=THRESHOLD_MONITORS, tbc=False)

    start_task.cancel()
