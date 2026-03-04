"""
TC_N_17 - Set Monitoring Level - Out of range
Use case: N05 | Requirements: N05.FR.02
N05.FR.02: When the Charging Station receives a setMonitoringLevelRequest for a severity that is out of range The Charging Station SHALL send a setMonitoringLevelResponse with Rejected .
    Precondition: When the Charging Station receives a setMonitoringLevelRequest for a severity that is out of range
System under test: CSMS

Description:
    CSMS sets a monitoring level.

Purpose:
    To test that CSMS supports the rejection of setting of a monitoring level.

Prerequisites:
    The OCTT will always reject the message, but normally this would only occur if the set
    severity level is out of range.

Main:
    1. CSMS sends SetMonitoringLevelRequest with severity = 4
    2. OCTT responds SetMonitoringLevelResponse with Status = Rejected

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
    GenericStatusEnumType,
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
async def test_tc_n_17():
    """Set Monitoring Level - Out of range."""
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

    # Configure CS to reject the SetMonitoringLevel request
    cp._set_monitoring_level_response_status = GenericStatusEnumType.rejected

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1-2: Wait for CSMS to send SetMonitoringLevelRequest
    # CS will respond with Rejected (configured above)
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

    # CS responded with Rejected (handled by on_set_monitoring_level handler)

    logging.info("TC_N_17 completed successfully")
    start_task.cancel()
    await ws.close()
