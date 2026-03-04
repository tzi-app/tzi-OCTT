"""
TC_N_02 - Get Monitoring Report - with component/variable
Use case: N02 | Requirements: N02.FR.05, N02.FR.10
N02.FR.05: N02.FR.01 AND monitoringCriteria and componentVariables are NOT both absent.
    Precondition: N02.FR.01 AND monitoringCriteria and componentVariables are NOT both absent.
N02.FR.10: When the Charging Station receives a GetMonitoringReportRequest for supported monitoringCriteria OR without monitoringCriteria, the Charging Station SHALL send a GetMonitoringReportResponse with status Accepted.
    Precondition: When the Charging Station receives a GetMonitoringReportRequest with a combination of criteria which results in an empty result set.
System under test: CSMS

Description:
    CSMS requests a report of monitors that match the given list of components and variables.

Purpose:
    To test that CSMS supports requesting a monitoring report filtered by component/variable
    and that it handles an empty result set.

Main:
    1. CSMS sends GetMonitoringReportRequest with componentVariable[0].component.name = "ChargingStation",
       componentVariable[0].variable.name = "Power"
    2. OCTT responds with GetMonitoringReportResponse status = EmptyResultSet
    3. CSMS sends GetMonitoringReportRequest with componentVariable[1].component.name = "EVSE",
       componentVariable[1].component.evse.id = 1, componentVariable[1].variable.name = "AvailabilityState"
    4. OCTT responds with GetMonitoringReportResponse status = Accepted
    5. OCTT sends NotifyMonitoringReportRequest
    6. CSMS sends NotifyMonitoringReportResponse

Tool validations:
    * Step 1: componentVariable[0].component.name = "ChargingStation",
              componentVariable[0].variable.name = "Power"
    * Step 3: componentVariable[1].component.name = "EVSE",
              componentVariable[1].component.evse.id = 1,
              componentVariable[1].variable.name = "AvailabilityState"

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    GenericDeviceModelStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_n_02():
    """Get Monitoring Report - with component/variable."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)

    # First request: ChargingStation/Power -> EmptyResultSet
    cp._get_monitoring_report_response_status = GenericDeviceModelStatusEnumType.empty_result_set

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1-2: Wait for CSMS to send GetMonitoringReportRequest (ChargingStation/Power)
    await asyncio.wait_for(
        cp._received_get_monitoring_report.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_monitoring_report_data is not None
    component_variable = cp._get_monitoring_report_data['component_variable']
    assert component_variable is not None, "componentVariable must be present"

    # Tool validation: monitoringCriteria is omitted
    monitoring_criteria = cp._get_monitoring_report_data.get('monitoring_criteria')
    assert monitoring_criteria is None, \
        f"Expected monitoringCriteria to be omitted (None), got {monitoring_criteria}"

    # Validate componentVariable[0]: ChargingStation / Power
    found_cs_power = False
    for cv in component_variable:
        comp = cv.get('component', {})
        var = cv.get('variable', {})
        if comp.get('name') == 'ChargingStation' and var.get('name') == 'Power':
            found_cs_power = True
            break
    assert found_cs_power, \
        f"Expected componentVariable with component.name=ChargingStation, variable.name=Power, got {component_variable}"

    logging.info("TC_N_02 step 1-2 completed: ChargingStation/Power -> EmptyResultSet")

    # Reset for next request
    cp._received_get_monitoring_report.clear()
    cp._get_monitoring_report_response_status = GenericDeviceModelStatusEnumType.accepted

    # Step 3-4: Wait for CSMS to send GetMonitoringReportRequest (EVSE/AvailabilityState)
    await asyncio.wait_for(
        cp._received_get_monitoring_report.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_monitoring_report_data is not None
    component_variable = cp._get_monitoring_report_data['component_variable']
    assert component_variable is not None, "componentVariable must be present"

    # Tool validation: monitoringCriteria is omitted
    monitoring_criteria = cp._get_monitoring_report_data.get('monitoring_criteria')
    assert monitoring_criteria is None, \
        f"Expected monitoringCriteria to be omitted (None), got {monitoring_criteria}"

    # Validate componentVariable: EVSE (evse.id=1) / AvailabilityState
    found_evse_avail = False
    for cv in component_variable:
        comp = cv.get('component', {})
        var = cv.get('variable', {})
        evse = comp.get('evse', {})
        if (comp.get('name') == 'EVSE'
                and evse.get('id') == 1
                and var.get('name') == 'AvailabilityState'):
            found_evse_avail = True
            break
    assert found_evse_avail, \
        f"Expected componentVariable with component.name=EVSE, evse.id=1, variable.name=AvailabilityState, got {component_variable}"

    request_id = cp._get_monitoring_report_data['request_id']

    # Step 5-6: CS sends NotifyMonitoringReportRequest
    await cp.send_notify_monitoring_report(
        request_id=request_id,
        seq_no=0,
        monitor=[{
            'component': {'name': 'EVSE', 'evse': {'id': 1}},
            'variable': {'name': 'AvailabilityState'},
            'variable_monitoring': [{
                'id': 1,
                'transaction': False,
                'value': 0.0,
                'type': 'Delta',
                'severity': 5,
            }],
        }],
    )

    logging.info("TC_N_02 completed successfully")
    start_task.cancel()
    await ws.close()
