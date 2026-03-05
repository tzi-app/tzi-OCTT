"""
TC_N_18 - Clear Monitoring - Too many elements
Use case: N06 | Requirements: N06.FR.04
N06.FR.04: The CSMS SHALL NOT put more id elements in a ClearVariableMonitoringRequest than reported by the Charging Station via: ItemsPerMessageClearVariableMonitoring and BytesPerMessageClearVariableMonitoring.
System under test: CSMS

Description:
    CSMS is requested to clear more monitors than allowed in one request.

Purpose:
    To test that CSMS does not exceed the ItemsPerMessageClearVariableMonitoring amount of
    monitors in one request.

Main:
    1. CSMS sends GetVariablesRequest with Component.name = MonitoringCtrlr,
       Variable.name = ItemsPerMessage, Variable.instance = ClearVariableMonitoring
    2. OCTT responds GetVariablesResponse
    3. CSMS sends ClearVariableMonitoringRequest with a list of ids
       (should NOT exceed ItemsPerMessage)
    4. OCTT responds ClearVariableMonitoringResponse for each

Tool validations:
    * Two or more ClearVariableMonitoringRequest, so ItemsPerMessageClearVariableMonitoring
      ids is never exceeded.
    * OCTT responds with ClearVariableMonitoringResponse for each request.

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
from utils import get_basic_auth_headers, build_default_ssl_context
from trigger import send_call

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_n_18():
    """Clear Monitoring - Too many elements."""
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

    # Set up response for GetVariables: ItemsPerMessage for ClearVariableMonitoring = 3
    items_per_message = 3
    cp._get_variables_values['MonitoringCtrlr.ItemsPerMessage'] = str(items_per_message)

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Trigger CSMS to send GetVariablesRequest
    await send_call(cp_id, "GetVariables", {
        "getVariableData": [{
            "component": {"name": "MonitoringCtrlr"},
            "variable": {"name": "ItemsPerMessage", "instance": "ClearVariableMonitoring"},
            "attributeType": "Actual",
        }],
    })

    # Step 1-2: Wait for CSMS to request the ItemsPerMessage variable
    await asyncio.wait_for(
        cp._received_get_variables.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_variables_data is not None
    logging.info(f"TC_N_18 step 1-2: GetVariablesRequest received: {cp._get_variables_data}")

    # Step 3-4: Wait for CSMS to send ClearVariableMonitoringRequest(s)
    # Collect all requests and validate each does not exceed ItemsPerMessage
    all_ids = []
    request_count = 0

    # Trigger CSMS to send first ClearVariableMonitoringRequest
    await send_call(cp_id, "ClearVariableMonitoring", {"id": [1, 2, 3]})

    await asyncio.wait_for(
        cp._received_clear_variable_monitoring.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    ids = cp._clear_variable_monitoring_data['id']
    assert len(ids) <= items_per_message, \
        f"ClearVariableMonitoringRequest has {len(ids)} ids, exceeds ItemsPerMessage={items_per_message}"
    all_ids.extend(ids)
    request_count += 1
    logging.info(f"TC_N_18 request {request_count}: {len(ids)} ids (limit={items_per_message})")

    # Check for additional ClearVariableMonitoringRequest(s)
    # Per spec: "Two or more ClearVariableMonitoringRequest" are expected
    cp._received_clear_variable_monitoring.clear()

    # Trigger CSMS to send second ClearVariableMonitoringRequest
    await send_call(cp_id, "ClearVariableMonitoring", {"id": [4, 5]})

    await asyncio.wait_for(
        cp._received_clear_variable_monitoring.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    ids = cp._clear_variable_monitoring_data['id']
    assert len(ids) <= items_per_message, \
        f"ClearVariableMonitoringRequest has {len(ids)} ids, exceeds ItemsPerMessage={items_per_message}"
    all_ids.extend(ids)
    request_count += 1
    logging.info(f"TC_N_18 request {request_count}: {len(ids)} ids (limit={items_per_message})")

    # Check for any further requests (optional)
    cp._received_clear_variable_monitoring.clear()
    try:
        await asyncio.wait_for(
            cp._received_clear_variable_monitoring.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )

        ids = cp._clear_variable_monitoring_data['id']
        assert len(ids) <= items_per_message, \
            f"ClearVariableMonitoringRequest has {len(ids)} ids, exceeds ItemsPerMessage={items_per_message}"
        all_ids.extend(ids)
        request_count += 1
        logging.info(f"TC_N_18 request {request_count}: {len(ids)} ids (limit={items_per_message})")
    except asyncio.TimeoutError:
        logging.info("No additional ClearVariableMonitoringRequest received")

    assert request_count >= 2, \
        f"Expected at least 2 ClearVariableMonitoringRequests, got {request_count}"

    logging.info(f"TC_N_18 completed: {request_count} request(s), {len(all_ids)} total ids cleared")
    start_task.cancel()
    await ws.close()
