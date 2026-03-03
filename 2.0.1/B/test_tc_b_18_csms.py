"""
Test case name      Get Custom Report - with componentCriteria and component/variables
Test case Id        TC_B_18_CSMS
Use case Id(s)      B08
Requirement(s)      B08.FR.01, B08.FR.03

Requirement Details:
    B08.FR.01: NOT B08.FR.15 AND NOT B08.FR.16 AND When the Charging Station receives a GetReportRequest for supported criteria The Charging Station SHALL send a GetReportResponse with Accepted
        Precondition: NOT B08.FR.15 AND NOT B08.FR.16 AND When the Charging Station receives a GetReportRequest for supported criteria
    B08.FR.03: The Charging Station SHALL respond with GetBaseReportResponse and start sending NotifyReportRequest messages.
        Precondition: B08.FR.01
System under test   CSMS

Description         CSMS requests a report of components that match both the component criteria
                    and the given list of components and variables.
Purpose             To test that CSMS supports requesting a report for both the component criteria and a given
                    list of components and optionally with variables and that it handles an empty result set.

Prerequisite(s)     N/a

Test Scenario
1. Manually instruct CSMS to get the value of:
   - EVSE #1::AvailabilityState
   - from all Problem components
   CSMS sends GetReportRequest with componentCriteria = Problem
2. OCTT responds with GetReportResponse with status EmptyResultSet

3. Manually instruct CSMS to get the value of:
   - EVSE #1::AvailabilityState
   - from all Available components
   CSMS sends GetReportRequest with componentCriteria = Available
4. OCTT responds with GetReportResponse with status Accepted

5. OCTT responds with NotifyReportRequest
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
import pytest
import os
import logging
from ocpp.v201.enums import (
    RegistrationStatusEnumType, ConnectorStatusEnumType,
    GenericDeviceModelStatusEnumType
)

from tzi_charge_point import TziChargePoint
from trigger import get_report
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_18(connection):
    """Get Custom Report - componentCriteria + component/variables with empty and non-empty results."""
    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    # First GetReport should return EmptyResultSet (Problem criteria)
    cp._get_report_response_status = GenericDeviceModelStatusEnumType.empty_result_set
    start_task = asyncio.create_task(cp.start())

    # Boot to establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    component_variable = [{
        "component": {"name": "EVSE", "evse": {"id": CONFIGURED_EVSE_ID}},
        "variable": {"name": "AvailabilityState"},
    }]

    # Step 1-2: Trigger GetReportRequest with componentCriteria = Problem
    trigger_task = asyncio.create_task(
        get_report(BASIC_AUTH_CP, ["Problem"], component_variable, request_id=1)
    )

    await asyncio.wait_for(
        cp._received_get_report.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task

    assert cp._get_report_data is not None
    report_data = cp._get_report_data
    logging.info(f"First GetReportRequest received: {report_data}")

    # Validate componentCriteria contains Problem
    component_criteria = report_data.get('component_criteria', report_data.get('componentCriteria', []))
    if isinstance(component_criteria, list):
        assert 'Problem' in component_criteria or any('Problem' in str(c) for c in component_criteria), \
            f"Expected Problem in componentCriteria, got: {component_criteria}"

    # Validate componentVariable fields for first request
    component_variable = report_data.get('component_variable', report_data.get('componentVariable', []))
    assert component_variable is not None and len(component_variable) >= 1, \
        f"Expected at least 1 componentVariable, got: {component_variable}"
    cv0 = component_variable[0]
    cv0_comp = cv0.get('component', {})
    cv0_var = cv0.get('variable', {})
    assert cv0_comp.get('name') == 'EVSE', \
        f"Expected componentVariable[0].component.name = 'EVSE', got: {cv0_comp.get('name')}"
    cv0_evse = cv0_comp.get('evse', {})
    assert cv0_evse.get('id') == CONFIGURED_EVSE_ID, \
        f"Expected componentVariable[0].component.evse.id = {CONFIGURED_EVSE_ID}, got: {cv0_evse.get('id')}"
    assert cv0_var.get('name') == 'AvailabilityState', \
        f"Expected componentVariable[0].variable.name = 'AvailabilityState', got: {cv0_var.get('name')}"

    # Step 3-4: Prepare for second GetReportRequest (componentCriteria = Available)
    cp._received_get_report.clear()
    cp._get_report_response_status = GenericDeviceModelStatusEnumType.accepted

    trigger_task2 = asyncio.create_task(
        get_report(BASIC_AUTH_CP, ["Available"], component_variable, request_id=2)
    )

    await asyncio.wait_for(
        cp._received_get_report.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task2

    report_data = cp._get_report_data
    logging.info(f"Second GetReportRequest received: {report_data}")

    # Validate componentCriteria contains Available for second request
    component_criteria_2 = report_data.get('component_criteria', report_data.get('componentCriteria', []))
    if isinstance(component_criteria_2, list):
        assert 'Available' in component_criteria_2 or any('Available' in str(c) for c in component_criteria_2), \
            f"Expected Available in componentCriteria, got: {component_criteria_2}"

    # Validate componentVariable fields for second request
    component_variable_2 = report_data.get('component_variable', report_data.get('componentVariable', []))
    assert component_variable_2 is not None and len(component_variable_2) >= 1, \
        f"Expected at least 1 componentVariable in second request, got: {component_variable_2}"
    cv0_2 = component_variable_2[0]
    cv0_comp_2 = cv0_2.get('component', {})
    cv0_var_2 = cv0_2.get('variable', {})
    assert cv0_comp_2.get('name') == 'EVSE', \
        f"Expected componentVariable[0].component.name = 'EVSE', got: {cv0_comp_2.get('name')}"
    cv0_evse_2 = cv0_comp_2.get('evse', {})
    assert cv0_evse_2.get('id') == CONFIGURED_EVSE_ID, \
        f"Expected componentVariable[0].component.evse.id = {CONFIGURED_EVSE_ID}, got: {cv0_evse_2.get('id')}"
    assert cv0_var_2.get('name') == 'AvailabilityState', \
        f"Expected componentVariable[0].variable.name = 'AvailabilityState', got: {cv0_var_2.get('name')}"

    # Step 5-6: Send NotifyReportRequest with matching data
    request_id = report_data.get('request_id', 0)
    notify_report_data = [{
        'component': {'name': 'EVSE', 'evse': {'id': CONFIGURED_EVSE_ID}},
        'variable': {'name': 'AvailabilityState'},
        'variable_attribute': [{
            'type': 'Actual',
            'value': 'Available',
            'mutability': 'ReadOnly',
        }],
        'variable_characteristics': {
            'data_type': 'OptionList',
            'supports_monitoring': True,
        },
    }]

    await cp.send_notify_report(
        request_id=request_id,
        seq_no=0,
        report_data=notify_report_data,
        tbc=False,
    )

    start_task.cancel()
