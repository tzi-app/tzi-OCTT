"""
TC_N_05 - Set Monitoring Base - success
Use case: N03 | Requirements: N03.FR.03, N03.FR.04, N03.FR.05
N03.FR.03: N03.FR.01 AND When the Charging Station received a SetMonitoringBaseRequest with monitoringBase All.
    Precondition: N03.FR.01 AND When the Charging Station received a setMonitoringBaseRequest with monitoringBase All
N03.FR.04: N03.FR.01 AND When the Charging Station received a SetMonitoringBaseRequest with monitoringBase FactoryDefault.
    Precondition: N03.FR.01 AND When the Charging Station received a setMonitoringBaseRequest with monitoringBase FactoryDefault
N03.FR.05: N03.FR.01 AND When the Charging Station received a SetMonitoringBaseRequest with monitoringBase HardWiredOnly.
    Precondition: N03.FR.01 AND When the Charging Station received a setMonitoringBaseRequest with monitoringBase HardWiredOnly
System under test: CSMS

Description:
    CSMS sends a SetMonitoringBaseRequest for All, FactoryDefault, HardWiredOnly.

Purpose:
    To test that CSMS supports all three monitoring base types.

Main:
    1. CSMS sends SetMonitoringBaseRequest with monitoringBase = All
    2. OCTT responds SetMonitoringBaseResponse
    3. CSMS sends SetMonitoringBaseRequest with monitoringBase = FactoryDefault
    4. OCTT responds SetMonitoringBaseResponse
    5. CSMS sends SetMonitoringBaseRequest with monitoringBase = HardWiredOnly
    6. OCTT responds SetMonitoringBaseResponse

Tool validations:
    * Step 1: monitoringBase = All
    * Step 3: monitoringBase = FactoryDefault
    * Step 5: monitoringBase = HardWiredOnly

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
    MonitorBaseEnumType,
    GenericDeviceModelStatusEnumType,
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
async def test_tc_n_05():
    """Set Monitoring Base - success."""
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
    cp._set_monitoring_base_response_status = GenericDeviceModelStatusEnumType.accepted

    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    monitoring_bases = [
        MonitorBaseEnumType.all,
        MonitorBaseEnumType.factory_default,
        MonitorBaseEnumType.hard_wired_only,
    ]
    monitoring_base_names = {
        MonitorBaseEnumType.all: "All",
        MonitorBaseEnumType.factory_default: "FactoryDefault",
        MonitorBaseEnumType.hard_wired_only: "HardWiredOnly",
    }

    for i, expected_base in enumerate(monitoring_bases):
        # Trigger CSMS to send SetMonitoringBaseRequest
        await send_call(cp_id, "SetMonitoringBase", {
            "monitoringBase": monitoring_base_names[expected_base],
        })

        # Wait for CSMS to send SetMonitoringBaseRequest
        await asyncio.wait_for(
            cp._received_set_monitoring_base.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )

        # Validate request content
        assert cp._set_monitoring_base_data is not None
        monitoring_base = cp._set_monitoring_base_data['monitoring_base']

        assert monitoring_base == expected_base, \
            f"Step {i * 2 + 1}: Expected monitoringBase={expected_base}, got {monitoring_base}"

        logging.info(f"TC_N_05 step {i + 1} ({expected_base}) completed successfully")

        # Reset event for next iteration
        cp._received_set_monitoring_base.clear()

    logging.info("TC_N_05 completed successfully")
    start_task.cancel()
    await ws.close()
