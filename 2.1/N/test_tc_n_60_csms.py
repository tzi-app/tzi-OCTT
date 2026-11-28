"""
Test case name      Get Monitoring Report - with component criteria and list of components/variables
Test case Id        TC_N_60_CSMS
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

Description         CSMS requests a report of monitors that match both the component criteria and the given
                    list of components and variables.

Purpose             To test that CSMS supports requesting a monitoring report for both the component criteria
                    and a given list of components and optionally with variables and that it handles an empty
                    result set.

Prerequisite(s)     CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.

Configuration State N/a

Memory State        CSMS requests ClearVariableMonitoring ItemsPerMessage from CS.

Reusable State(s)   N/a

Test Scenario
Manual Action: Manually instruct CSMS to get a report of monitors for:
- all ThresholdMonitoring
- and the variable Power of both ChargingStation and EVSE #1.

1. CSMS sends GetMonitoringReportRequest
2. Test System responds with:
    GetMonitoringReportResponse with:
    - Status EmptyResultSet

Manual Action: Manually instruct CSMS to get a report of monitors for:
- all DeltaMonitoring
- and the variable AvailabilityState of both ChargingStation and EVSE #1.

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
    - monitoringCriteria is DeltaMonitoring
    - componentVariable[0].component.name = "ChargingStation"
    - componentVariable[0].variable.name = "AvailabilityState"
    - componentVariable[1].component.name = "EVSE"
    - componentVariable[1].component.evse.id = <configured evseId>
    - componentVariable[1].variable.name = "AvailabilityState"
* Step 3:
    Message: GetMonitoringReportRequest
    - monitoringCriteria = ThresholdMonitoring
    - componentVariable[0].component.name = "ChargingStation"
    - componentVariable[0].variable.name = "AvailabilityState"
    - componentVariable[1].component.name = "EVSE"
    - componentVariable[1].component.evse.id = <configured evseId>
    - componentVariable[1].variable.name = "AvailabilityState"

Post scenario validations:
    Check that CSMS shows the Delta monitors for AvailabilityState for both ChargingStation and EVSE #1.
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from monitoring import (
    component_variable,
    csms_requests_items_per_message,
    DELTA_MONITORS,
    MONITORING_VARIABLES,
    request_monitoring_report,
    validate_component_variable,
    validate_monitoring_criteria,
)
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_60(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisite: CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.
    cp.variables = dict(MONITORING_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # The Manual Actions of this test case and its tool validations do not name the same
    # criteria and variables. The requests are the ones of the tool validations.
    both = [component_variable('ChargingStation', 'AvailabilityState'),
            component_variable('EVSE', 'AvailabilityState', evse_id=CONFIGURED_EVSE_ID)]

    # Memory State: CSMS requests ClearVariableMonitoring ItemsPerMessage from CS.
    await csms_requests_items_per_message(cp)

    # Manual Action: Manually instruct CSMS to get a report of monitors for a monitoring criterion
    #                and the variable of both ChargingStation and EVSE #1.
    # 1. CSMS sends GetMonitoringReportRequest
    #    - monitoringCriteria is DeltaMonitoring
    #    - componentVariable[0]: component.name "ChargingStation", variable.name
    #      "AvailabilityState"
    #    - componentVariable[1]: component.name "EVSE", component.evse.id <configured evseId>,
    #      variable.name "AvailabilityState"
    # 2. Test System responds with: GetMonitoringReportResponse with:
    #    - Status EmptyResultSet
    request = await request_monitoring_report(
        cp, 'EmptyResultSet', monitoring_criteria=['DeltaMonitoring'], component_variables=both,
        request_id=1)
    validate_monitoring_criteria(request, 'DeltaMonitoring')
    validate_component_variable(request, 0, 'ChargingStation', 'AvailabilityState')
    validate_component_variable(request, 1, 'EVSE', 'AvailabilityState', evse_id=CONFIGURED_EVSE_ID)

    # Manual Action: Manually instruct CSMS to get a report of monitors for the other monitoring
    #                criterion and the variable of both ChargingStation and EVSE #1.
    # 3. CSMS sends GetMonitoringReportRequest
    #    - monitoringCriteria = ThresholdMonitoring
    #    - componentVariable[0] and [1] as in step 1
    # 4. Test System responds with: GetMonitoringReportResponse with:
    #    - Status Accepted
    request = await request_monitoring_report(
        cp, 'Accepted', monitoring_criteria=['ThresholdMonitoring'], component_variables=both,
        request_id=2)
    validate_monitoring_criteria(request, 'ThresholdMonitoring')
    validate_component_variable(request, 0, 'ChargingStation', 'AvailabilityState')
    validate_component_variable(request, 1, 'EVSE', 'AvailabilityState', evse_id=CONFIGURED_EVSE_ID)

    # 5. Test System responds with: NotifyMonitoringReportRequest
    # 6. CSMS sends NotifyMonitoringReportResponse
    # Step 5 and 6 are repeated as often as needed to report all configuration variables.
    await cp.send_notify_monitoring_report(request.request_id, seq_no=0, monitor=DELTA_MONITORS)
    # "Check that CSMS shows the monitors for AvailabilityState for both ChargingStation and EVSE
    # #1" is a check in the CSMS itself.

    start_task.cancel()
