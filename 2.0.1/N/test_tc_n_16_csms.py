"""
TC_N_16 - Set Monitoring Level - Success
Use case: N05 | Requirements: N05.FR.01
N05.FR.01: When the Charging Station accepts a setMonitoringLevelRequest The Charging Station SHALL send a setMonitoringLevelResponse with Accepted.
    Precondition: When the Charging Station accepts a setMonitoringLevelRequest
System under test: CSMS

Description:
    CSMS sets a monitoring level.

Purpose:
    To test that CSMS supports setting of a monitoring level.

Main:
    1. CSMS sends SetMonitoringLevelRequest with severity = 4
    2. OCTT responds SetMonitoringLevelResponse with Status = Accepted

Tool validations:
    * Step 1: severity = 4

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
async def test_tc_n_16():
    """Set Monitoring Level - Success."""
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
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Trigger CSMS to send SetMonitoringLevelRequest
    await send_call(cp_id, "SetMonitoringLevel", {"severity": 4})

    # Step 1-2: Wait for CSMS to send SetMonitoringLevelRequest
    # Default response status is GenericStatusEnumType.accepted
    await asyncio.wait_for(
        cp._received_set_monitoring_level.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate SetMonitoringLevelRequest content
    assert cp._set_monitoring_level_data is not None
    severity = cp._set_monitoring_level_data['severity']

    # Tool validation: severity = 4
    assert severity == 4, \
        f"Expected severity=4, got {severity}"

    # CS responded with Accepted (handled by on_set_monitoring_level handler)

    logging.info("TC_N_16 completed successfully")
    start_task.cancel()
    await ws.close()
