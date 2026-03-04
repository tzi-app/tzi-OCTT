"""
TC_N_44 - Clear Monitoring - Rejected
Use case: N06 | Requirements: N/a
System under test: CSMS

Description:
    CSMS sends a ClearVariableMonitoringRequest to clear one or more monitors.
    The Charging Station responds with clearMonitoringResult[0].status = Rejected.

Purpose:
    To verify that the CSMS correctly handles a ClearVariableMonitoringResponse
    where the Charging Station rejects the clearing of monitoring.

Main:
    1. CSMS sends ClearVariableMonitoringRequest
    2. OCTT responds ClearVariableMonitoringResponse with
       clearMonitoringResult[0].status = Rejected

Tool validations:
    N/a

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
    ClearMonitoringStatusEnumType,
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
async def test_tc_n_44():
    """Clear Monitoring - Rejected."""
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

    # Pre-set response to Rejected for all clearing attempts
    cp._clear_variable_monitoring_response_results = [
        ClearMonitoringStatusEnumType.rejected,
    ]

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Trigger CSMS to send ClearVariableMonitoringRequest
    await send_call(cp_id, "ClearVariableMonitoring", {"id": [1]})

    # Step 1-2: Wait for CSMS to send ClearVariableMonitoringRequest
    await asyncio.wait_for(
        cp._received_clear_variable_monitoring.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    data = cp._clear_variable_monitoring_data
    assert data is not None, "ClearVariableMonitoringRequest data must be present"

    ids = data['id']
    assert ids is not None and len(ids) > 0, \
        "ClearVariableMonitoringRequest must contain at least one id"

    logging.info(f"TC_N_44 step 1-2 completed: ClearVariableMonitoringRequest received "
                 f"with ids={ids}, responded with Rejected")

    logging.info("TC_N_44 completed successfully")
    start_task.cancel()
    await ws.close()
