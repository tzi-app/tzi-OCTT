"""
Test case name      Get Base Report - ConfigurationInventory
Test case Id        TC_B_12_CSMS
Use case Id(s)      B07
Requirement(s)      B07.FR.07

Requirement Details:
    B07.FR.07: Then the Charging Station SHALL respond with a NotifyReportRequest to report on all
               component-variables that can be set by the operator including their VariableCharacteristics.
        Precondition: B07.FR.01 AND When reportBase is ConfigurationInventory
System under test   CSMS

Description         CSMS requests a ConfigurationInventory base report.

Purpose             To test that CSMS supports the ConfigurationInventory base report.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. (CSMS) Manually instruct CSMS to retrieve a ConfigurationInventory report.
2. (Charging Station) Test System responds with:
    GetBaseReportResponse

Tool validations
* Step 1:
    Message: GetBaseReportRequest with:
    - requestId has integer value >= 0
    - reportBase = ConfigurationInventory

Post scenario validations:
    CSMS receives all NotifyReportRequest message for this requestId and is able to show the result of
    configuration inventory to an operator.
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from device_model import CONFIGURATION_INVENTORY, send_report
from reusable_states.booted import booted
from trigger import get_base_report
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_12(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Manually instruct CSMS to retrieve a ConfigurationInventory report.
    # 2. Test System responds with: GetBaseReportResponse
    request = await cp.wait_for_request(
        'GetBaseReport',
        manual_action=get_base_report(BASIC_AUTH_CP, 'ConfigurationInventory'))

    assert isinstance(request.request_id, int) and request.request_id >= 0, \
        f"requestId must have an integer value >= 0, got: {request.request_id}"
    assert request.report_base == 'ConfigurationInventory', \
        f"Expected reportBase ConfigurationInventory, got: {request.report_base}"

    # The CSMS receives all NotifyReportRequest messages for this requestId. That it is able
    # to show the configuration inventory to an operator is a check on the CSMS itself.
    await send_report(cp, request.request_id, CONFIGURATION_INVENTORY)

    start_task.cancel()
