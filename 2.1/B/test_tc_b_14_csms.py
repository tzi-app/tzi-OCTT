"""
Test case name      Get Base Report - SummaryInventory
Test case Id        TC_B_14_CSMS
Use case Id(s)      B07
Requirement(s)      B07.FR.09

Requirement Details:
    B07.FR.09: Then the Charging Station SHALL respond with a NotifyReportRequest to report on components and
               variables related to the availability and condition of the Charging Station, notably
               operationalStatus of the Charging Station, EVSE and Connectors and any error condition.
        Precondition: B07.FR.01 AND When reportBase is SummaryInventory
        Note: A (summary) report that lists Components/Variables relating to the Charging Station’s current
              charging availability, and to any existing problem conditions. For the Charging Station
              Component:
              - AvailabilityState.
              For each EVSE Component:
              - AvailabilityState.
              For each Connector Component:
              - AvailabilityState (if known and different from EVSE).
              For all Components in an abnormal State:
              - Active (Problem, Tripped, Overload, Fallback) variables.
              - Any other diagnostically relevant Variables of the Components.
System under test   CSMS

Description         CSMS requests a SummaryInventory base report.

Purpose             To test that CSMS supports the SummaryInventory base report.

Prerequisite(s)     CSMS implementation supports the optional SummaryInventory report

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Manually instruct CSMS to retrieve a SummaryInventory report.
2. Test System responds with:
    GetBaseReportResponse

Tool validations
* Step 1:
    GetBaseReportRequest with:
    - requestId has integer value >= 0
    - reportBase = SummaryInventory

Post scenario validations:
    CSMS receives all NotifyReportRequest message for this requestId and is able to show the result of summary
    inventory to an operator.
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from device_model import SUMMARY_INVENTORY, send_report
from reusable_states.booted import booted
from trigger import get_base_report
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_14(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Manually instruct CSMS to retrieve a SummaryInventory report.
    # 2. Test System responds with: GetBaseReportResponse
    request = await cp.wait_for_request(
        'GetBaseReport',
        manual_action=get_base_report(BASIC_AUTH_CP, 'SummaryInventory'))

    assert isinstance(request.request_id, int) and request.request_id >= 0, \
        f"requestId must have an integer value >= 0, got: {request.request_id}"
    assert request.report_base == 'SummaryInventory', \
        f"Expected reportBase SummaryInventory, got: {request.report_base}"

    # The CSMS receives all NotifyReportRequest messages for this requestId. That it is able
    # to show the summary inventory to an operator is a check on the CSMS itself.
    await send_report(cp, request.request_id, SUMMARY_INVENTORY)

    start_task.cancel()
