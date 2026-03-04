"""
TC_N_03 - Get Monitoring Report - with component criteria and component/variable
Use case: N02 | Requirements: N02.FR.05, N02.FR.10
N02.FR.05: N02.FR.01 AND monitoringCriteria and componentVariables are NOT both absent.
    Precondition: N02.FR.01 AND monitoringCriteria and componentVariables are NOT both absent.
N02.FR.10: When the Charging Station receives a GetMonitoringReportRequest for supported monitoringCriteria OR without monitoringCriteria, the Charging Station SHALL send a GetMonitoringReportResponse with status Accepted.
    Precondition: When the Charging Station receives a GetMonitoringReportRequest with a combination of criteria which results in an empty result set.
System under test: CSMS

Description:
    CSMS requests a report of monitors that match both the component criteria and the given
    list of components and variables.

Purpose:
    To test that CSMS supports requesting a monitoring report filtered by both monitoringCriteria
    and componentVariable, and that it handles an empty result set.

Main:
    1. CSMS sends GetMonitoringReportRequest with monitoringCriteria = DeltaMonitoring AND
       componentVariable[0].component.name = "EVSE", componentVariable[0].component.evse.id = <configured>,
       componentVariable[0].variable.name = "AvailabilityState"
    2. OCTT responds with GetMonitoringReportResponse status = EmptyResultSet
    3. CSMS sends GetMonitoringReportRequest with monitoringCriteria = ThresholdMonitoring AND
       componentVariable[0].component.name = "ChargingStation",
       componentVariable[0].variable.name = "Power"
    4. OCTT responds with GetMonitoringReportResponse status = Accepted
    5. OCTT sends NotifyMonitoringReportRequest
    6. CSMS sends NotifyMonitoringReportResponse

Tool validations:
    * Step 1: monitoringCriteria = DeltaMonitoring,
              componentVariable[0].component.name = "EVSE",
              componentVariable[0].component.evse.id = <configured evseId>,
              componentVariable[0].variable.name = "AvailabilityState"
    * Step 3: monitoringCriteria = ThresholdMonitoring,
              componentVariable[0].component.name = "ChargingStation",
              componentVariable[0].variable.name = "Power"

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
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
    MonitoringCriterionEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, build_default_ssl_context
from trigger import send_call

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_n_03():
    """Get Monitoring Report - with component criteria and component/variable."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)

    # First request: DeltaMonitoring + EVSE/AvailabilityState -> EmptyResultSet
    cp._get_monitoring_report_response_status = GenericDeviceModelStatusEnumType.empty_result_set

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Trigger CSMS to send GetMonitoringReportRequest (DeltaMonitoring + EVSE/AvailabilityState)
    await send_call(cp_id, "GetMonitoringReport", {
        "requestId": 1,
        "monitoringCriteria": ["DeltaMonitoring"],
        "componentVariable": [{"component": {"name": "EVSE", "evse": {"id": CONFIGURED_EVSE_ID}}, "variable": {"name": "AvailabilityState"}}],
    })

    # Step 1-2: Wait for CSMS to send GetMonitoringReportRequest (DeltaMonitoring + EVSE/AvailabilityState)
    await asyncio.wait_for(
        cp._received_get_monitoring_report.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_monitoring_report_data is not None

    # Validate monitoringCriteria = DeltaMonitoring
    criteria = cp._get_monitoring_report_data['monitoring_criteria']
    assert criteria is not None, "monitoringCriteria must be present"
    if isinstance(criteria, list):
        assert MonitoringCriterionEnumType.delta_monitoring in criteria, \
            f"Expected DeltaMonitoring in criteria, got {criteria}"
    else:
        assert criteria == MonitoringCriterionEnumType.delta_monitoring

    # Validate componentVariable: EVSE (evse.id=configured) / AvailabilityState
    component_variable = cp._get_monitoring_report_data['component_variable']
    assert component_variable is not None, "componentVariable must be present"

    found_evse_avail = False
    for cv in component_variable:
        comp = cv.get('component', {})
        var = cv.get('variable', {})
        evse = comp.get('evse', {})
        if (comp.get('name') == 'EVSE'
                and evse.get('id') == CONFIGURED_EVSE_ID
                and var.get('name') == 'AvailabilityState'):
            found_evse_avail = True
            break
    assert found_evse_avail, \
        f"Expected componentVariable with component.name=EVSE, evse.id={CONFIGURED_EVSE_ID}, " \
        f"variable.name=AvailabilityState, got {component_variable}"

    logging.info("TC_N_03 step 1-2 completed: DeltaMonitoring + EVSE/AvailabilityState -> EmptyResultSet")

    # Reset for next request
    cp._received_get_monitoring_report.clear()
    cp._get_monitoring_report_response_status = GenericDeviceModelStatusEnumType.accepted

    # Trigger CSMS to send GetMonitoringReportRequest (ThresholdMonitoring + ChargingStation/Power)
    await send_call(cp_id, "GetMonitoringReport", {
        "requestId": 2,
        "monitoringCriteria": ["ThresholdMonitoring"],
        "componentVariable": [{"component": {"name": "ChargingStation"}, "variable": {"name": "Power"}}],
    })

    # Step 3-4: Wait for CSMS to send GetMonitoringReportRequest (ThresholdMonitoring + ChargingStation/Power)
    await asyncio.wait_for(
        cp._received_get_monitoring_report.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_monitoring_report_data is not None

    # Validate monitoringCriteria = ThresholdMonitoring
    criteria = cp._get_monitoring_report_data['monitoring_criteria']
    assert criteria is not None, "monitoringCriteria must be present"
    if isinstance(criteria, list):
        assert MonitoringCriterionEnumType.threshold_monitoring in criteria, \
            f"Expected ThresholdMonitoring in criteria, got {criteria}"
    else:
        assert criteria == MonitoringCriterionEnumType.threshold_monitoring

    # Validate componentVariable: ChargingStation / Power
    component_variable = cp._get_monitoring_report_data['component_variable']
    assert component_variable is not None, "componentVariable must be present"

    found_cs_power = False
    for cv in component_variable:
        comp = cv.get('component', {})
        var = cv.get('variable', {})
        if comp.get('name') == 'ChargingStation' and var.get('name') == 'Power':
            found_cs_power = True
            break
    assert found_cs_power, \
        f"Expected componentVariable with component.name=ChargingStation, variable.name=Power, got {component_variable}"

    request_id = cp._get_monitoring_report_data['request_id']

    # Step 5-6: CS sends NotifyMonitoringReportRequest
    await cp.send_notify_monitoring_report(
        request_id=request_id,
        seq_no=0,
        monitor=[{
            'component': {'name': 'ChargingStation'},
            'variable': {'name': 'Power'},
            'variable_monitoring': [{
                'id': 1,
                'transaction': False,
                'value': 100.0,
                'type': 'UpperThreshold',
                'severity': 5,
            }],
        }],
    )

    logging.info("TC_N_03 completed successfully")
    start_task.cancel()
    await ws.close()
