"""
Test case name      Set Variable Monitoring - One SetMonitoringData element
Test case Id        TC_N_08_CSMS
Use case Id(s)      N04
Requirement(s)      N04.FR.01, N04.FR.02, N04.FR.17

Requirement Details:
    N04.FR.01: The Charging Station SHALL respond with an SetVariableMonitoringResponse with an equal (X)
               number of SetMonitoringResult elements, one for every SetMonitoringData element in the
               SetVariableMonitoringRequest.
        Precondition: When the Charging Station receives a SetVariableMonitoringRequest with an X number of
                      SetMonitoringData elements
    N04.FR.02: Every SetMonitoringResult element in the SetVariableMonitoringResponse SHALL contain the same
               component and variable combination as one of the SetVariableMonitoringRequest elements in the
               SetVariableMonitoringRequest.
        Precondition: N04.FR.01
    N04.FR.17: It is RECOMMENDED to use a value of 1.
        Precondition: When the CSMS sends a SetVariableMonitoringRequest with type Delta for a Variable that
                      is NOT of a numeric type
        Note: value is irrelevant for non-numeric types (e.g. any type except decimal or integer), since the
              monitor is triggered by every change of the Variable.
System under test   CSMS

Description         CSMS sends a request to activate monitoring on one variable.

Purpose             To test that CSMS supports setting monitoring on one variable.

Prerequisite(s)     CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.

Configuration State This test case activates monitoring on the following variable:
                    - Component "EVSE", evse <Configured evseId>, variable "AvailabilityState", monitor type
                      Delta
                    It assumes, that no monitor is active on this variable prior to the test.
                    Note 1: this is a required variable for which a monitor can be expected to exist or it can
                    be configured.
                    Note 2: Any other component/variable combination that supports monitoring could also be
                    used for this test case.

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. [CSMS] Request CSMS to install monitors on:
    - EVSE #<Configured evseId>, AvailabilityState, Delta, severity 8
2. [Charging Station] Test System responds with:
    Message: SetVariableMonitoringResponse with
    setMonitoringResult[0].status = Accepted

Tool validations
* Step 1:
    1. CSMS sends SetVariableMonitoringRequest with:
    - setMonitoringData[0].value = 1, ← recommended value for Delta monitor
    - setMonitoringData[0].type = Delta,
    - setMonitoringData[0].severity = 8,
    - setMonitoringData[0].component.name = "EVSE"
    - setMonitoringData[0].component.evse.id = <Configured evseId>
    - setMonitoringData[0].variable.name = "AvailabilityState"

Post scenario validations:
    N/A
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from monitoring import MONITORING_VARIABLES
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_08(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisite: CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.
    cp.variables = dict(MONITORING_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Request CSMS to install monitors on:
    #    - EVSE #<Configured evseId>, AvailabilityState, Delta, severity 8
    # 2. Test System responds with: SetVariableMonitoringResponse with
    #    setMonitoringResult[0].status = Accepted
    request = await cp.wait_for_request(
        'SetVariableMonitoring',
        manual_action=send_call(BASIC_AUTH_CP, 'SetVariableMonitoring', {'setMonitoringData': [{
            'value': 1,
            'type': 'Delta',
            'severity': 8,
            'component': {'name': 'EVSE', 'evse': {'id': CONFIGURED_EVSE_ID}},
            'variable': {'name': 'AvailabilityState'},
        }]}))
    monitor = request.set_monitoring_data[0]
    # setMonitoringData[0].value = 1 (the recommended value for a Delta monitor)
    assert monitor.value == 1, f"Expected setMonitoringData[0].value 1, got {monitor.value}"
    assert monitor.type == 'Delta', f"Expected setMonitoringData[0].type Delta, got {monitor.type}"
    assert monitor.severity == 8, f"Expected setMonitoringData[0].severity 8, got {monitor.severity}"
    assert monitor.component.name == 'EVSE', \
        f"Expected setMonitoringData[0].component.name EVSE, got {monitor.component.name}"
    assert monitor.component.evse is not None and monitor.component.evse.id == CONFIGURED_EVSE_ID, \
        f"Expected setMonitoringData[0].component.evse.id {CONFIGURED_EVSE_ID}, got {monitor.component.evse}"
    assert monitor.variable.name == 'AvailabilityState', \
        f"Expected setMonitoringData[0].variable.name AvailabilityState, got {monitor.variable.name}"

    start_task.cancel()
