"""
Test case name      Get Custom Report - with componentCriteria and component/variables
Test case Id        TC_B_18_CSMS
Use case Id(s)      B08
Requirement(s)      B08.FR.01, B08.FR.03

Requirement Details:
    B08.FR.01: The Charging Station SHALL send a GetReportResponse with Accepted
        Precondition: NOT B08.FR.15 AND NOT B08.FR.16 AND When the Charging Station receives a
                      GetReportRequest for supported criteria
    B08.FR.03: The Charging Station SHALL send the requested information, excluding the value of WriteOnly
               variables, via one or more NotifyReportRequest messages to the CSMS.
        Precondition: B08.FR.01
System under test   CSMS

Description         CSMS requests a report of components that match both the component criteria
                    and the given list of components and variables.

Purpose             To test that CSMS supports requesting a report for both the component criteria and a given
                    list of components and optionally with variables and that it handles an empty result set.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Manually instruct CSMS to get the value of:
    - EVSE #1::AvailabiltyState
    - from all Problem components
2. Test System responds with:
    GetReportResponse with
    status EmptyResultSet
3. Manually instruct CSMS to get the value of:
    - EVSE #1::AvailabiltyState
    - from all Available components
4. Test System responds with:
    GetReportResponse with
    status Accepted
5. Test System responds with:
    NotifyReportRequest
6. CSMS sends NotifyReportResponse

Tool validations
* Step 1:
    Message: GetReportRequest
    - componentCriteria = Problem
    - componentVariable[0].component.name = "EVSE"
    - componentVariable[0].component.evse.id = 1
    - componentVariable[0].variable.name = "AvailabilityState"
* Step 3:
    Message: GetReportRequest
    - componentCriteria is Available
    - componentVariable[0].component.name = "EVSE"
    - componentVariable[0].component.evse.id = 1
    - componentVariable[0].variable.name = "AvailabilityState"

Post scenario validations:
    N/A
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import get_report
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

# EVSE #1::AvailabilityState
COMPONENT_VARIABLE = [{
    'component': {'name': 'EVSE', 'evse': {'id': 1}},
    'variable': {'name': 'AvailabilityState'},
}]


def _validate_get_report_request(request, component_criterion):
    assert request.component_criteria == [component_criterion], \
        f"Expected componentCriteria {component_criterion}, got: {request.component_criteria}"
    assert request.component_variable, "Expected a componentVariable in the GetReportRequest"
    component_variable = request.component_variable[0]
    assert component_variable.component.name == 'EVSE', \
        f"Expected componentVariable[0].component.name EVSE, got: {component_variable.component.name}"
    assert component_variable.component.evse is not None and component_variable.component.evse.id == 1, \
        f"Expected componentVariable[0].component.evse.id 1, got: {component_variable.component.evse}"
    assert component_variable.variable is not None \
        and component_variable.variable.name == 'AvailabilityState', \
        f"Expected componentVariable[0].variable.name AvailabilityState, got: {component_variable.variable}"


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_18(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Manually instruct CSMS to get the value of EVSE #1::AvailabilityState from all
    #    Problem components
    # 2. Test System responds with: GetReportResponse with status EmptyResultSet
    cp.set_response('GetReport', status='EmptyResultSet')
    request = await cp.wait_for_request(
        'GetReport',
        manual_action=get_report(BASIC_AUTH_CP, ['Problem'], COMPONENT_VARIABLE, request_id=1))
    _validate_get_report_request(request, 'Problem')

    # 3. Manually instruct CSMS to get the value of EVSE #1::AvailabilityState from all
    #    Available components
    # 4. Test System responds with: GetReportResponse with status Accepted
    cp.set_response('GetReport', status='Accepted')
    request = await cp.wait_for_request(
        'GetReport',
        manual_action=get_report(BASIC_AUTH_CP, ['Available'], COMPONENT_VARIABLE, request_id=2))
    _validate_get_report_request(request, 'Available')

    # 5. Test System responds with: NotifyReportRequest
    # 6. CSMS sends NotifyReportResponse
    await cp.send_notify_report(
        request_id=request.request_id,
        seq_no=0,
        report_data=[{
            'component': {'name': 'EVSE', 'evse': {'id': 1}},
            'variable': {'name': 'AvailabilityState'},
            'variable_attribute': [{'type': 'Actual', 'value': 'Available', 'mutability': 'ReadOnly'}],
            'variable_characteristics': {
                'data_type': 'OptionList',
                'supports_monitoring': True,
                'values_list': 'Available,Occupied,Reserved,Unavailable,Faulted',
            },
        }],
        tbc=False,
    )

    start_task.cancel()
