"""
TC_N_01 - Get Monitoring Report - with monitoringCriteria
Use case: N02 | Requirements: N02.FR.05, N02.FR.10
N02.FR.05: N02.FR.01 AND monitoringCriteria and componentVariables are NOT both absent.
    Precondition: N02.FR.01 AND monitoringCriteria and componentVariables are NOT both absent.
N02.FR.10: When the Charging Station receives a GetMonitoringReportRequest for supported monitoringCriteria OR without monitoringCriteria, the Charging Station SHALL send a GetMonitoringReportResponse with status Accepted.
    Precondition: When the Charging Station receives a GetMonitoringReportRequest with a combination of criteria which results in an empty result set.
System under test: CSMS

Description:
    CSMS requests a report of monitors that match the component criteria.

Purpose:
    To test that CSMS supports requesting a monitoring report for the component criteria and that it handles
    an empty result set.

Main:
    1. CSMS sends GetMonitoringReportRequest with monitoringCriteria = DeltaMonitoring
    2. OCTT responds with GetMonitoringReportResponse status = EmptyResultSet
    3. CSMS sends GetMonitoringReportRequest with monitoringCriteria = ThresholdMonitoring
    4. OCTT responds with GetMonitoringReportResponse status = Accepted
    5. OCTT sends NotifyMonitoringReportRequest
    6. CSMS sends NotifyMonitoringReportResponse

Tool validations:
    * Step 1: monitoringCriteria = DeltaMonitoring
    * Step 3: monitoringCriteria = ThresholdMonitoring

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
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_n_01():
    """Get Monitoring Report - with monitoringCriteria."""
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

    # First request: DeltaMonitoring -> EmptyResultSet
    cp._get_monitoring_report_response_status = GenericDeviceModelStatusEnumType.empty_result_set

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Trigger CSMS to send GetMonitoringReportRequest (DeltaMonitoring)
    await send_call(cp_id, "GetMonitoringReport", {
        "requestId": 1,
        "monitoringCriteria": ["DeltaMonitoring"],
    })

    # Step 1-2: Wait for CSMS to send GetMonitoringReportRequest (DeltaMonitoring)
    await asyncio.wait_for(
        cp._received_get_monitoring_report.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_monitoring_report_data is not None
    criteria = cp._get_monitoring_report_data['monitoring_criteria']
    assert criteria is not None, "monitoringCriteria must be present"
    if isinstance(criteria, list):
        assert MonitoringCriterionEnumType.delta_monitoring in criteria, \
            f"Expected DeltaMonitoring in criteria, got {criteria}"
    else:
        assert criteria == MonitoringCriterionEnumType.delta_monitoring

    # Tool validation: componentVariable is omitted
    component_variable = cp._get_monitoring_report_data.get('component_variable')
    assert component_variable is None, \
        f"Expected componentVariable to be omitted (None), got {component_variable}"

    logging.info("TC_N_01 step 1-2 completed: DeltaMonitoring -> EmptyResultSet")

    # Reset for next request
    cp._received_get_monitoring_report.clear()
    cp._get_monitoring_report_response_status = GenericDeviceModelStatusEnumType.accepted

    # Trigger CSMS to send GetMonitoringReportRequest (ThresholdMonitoring)
    await send_call(cp_id, "GetMonitoringReport", {
        "requestId": 2,
        "monitoringCriteria": ["ThresholdMonitoring"],
    })

    # Step 3-4: Wait for CSMS to send GetMonitoringReportRequest (ThresholdMonitoring)
    await asyncio.wait_for(
        cp._received_get_monitoring_report.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_monitoring_report_data is not None
    criteria = cp._get_monitoring_report_data['monitoring_criteria']
    assert criteria is not None, "monitoringCriteria must be present"
    if isinstance(criteria, list):
        assert MonitoringCriterionEnumType.threshold_monitoring in criteria, \
            f"Expected ThresholdMonitoring in criteria, got {criteria}"
    else:
        assert criteria == MonitoringCriterionEnumType.threshold_monitoring

    # Tool validation: componentVariable is omitted
    component_variable = cp._get_monitoring_report_data.get('component_variable')
    assert component_variable is None, \
        f"Expected componentVariable to be omitted (None), got {component_variable}"

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

    logging.info("TC_N_01 completed successfully")
    start_task.cancel()
    await ws.close()
