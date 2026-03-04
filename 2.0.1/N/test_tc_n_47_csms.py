"""
TC_N_47 - Get Monitoring report - Report all
Use case: N02 | Requirements: N/a
System under test: CSMS

Description:
    CSMS sends GetMonitoringReportRequest with both monitoringCriteria
    and componentVariable omitted, requesting a report of all monitors.

Purpose:
    To test that CSMS supports sending a GetMonitoringReportRequest with
    monitoringCriteria omitted and componentVariable omitted, and that the
    CSMS correctly handles the NotifyMonitoringReport sent back by the
    Charging Station.

Main:
    1. CSMS sends GetMonitoringReportRequest (monitoringCriteria omitted,
       componentVariable omitted)
    2. OCTT responds GetMonitoringReportResponse (status = Accepted)
    3. OCTT sends NotifyMonitoringReportRequest
    4. CSMS responds NotifyMonitoringReportResponse
    Note: If tbc is True at Step 3, steps 3 and 4 will be repeated

Tool validations:
    * Step 1: monitoringCriteria omitted AND componentVariable omitted

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
async def test_tc_n_47():
    """Get Monitoring report - Report all."""
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

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1-2: Wait for CSMS to send GetMonitoringReportRequest
    await asyncio.wait_for(
        cp._received_get_monitoring_report.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_monitoring_report_data is not None

    # Validate monitoringCriteria is omitted (None)
    monitoring_criteria = cp._get_monitoring_report_data.get('monitoring_criteria')
    assert monitoring_criteria is None, \
        f"Expected monitoringCriteria to be omitted (None), got {monitoring_criteria}"

    # Validate componentVariable is omitted (None)
    component_variable = cp._get_monitoring_report_data.get('component_variable')
    assert component_variable is None, \
        f"Expected componentVariable to be omitted (None), got {component_variable}"

    request_id = cp._get_monitoring_report_data['request_id']

    logging.info("TC_N_47 step 1-2 completed: GetMonitoringReportResponse Accepted")

    # Step 3-4: OCTT sends NotifyMonitoringReportRequest
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

    logging.info("TC_N_47 completed successfully")
    start_task.cancel()
    await ws.close()
