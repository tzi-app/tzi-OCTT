"""
TC_N_08 - Set Variable Monitoring - One SetMonitoringData element
Use case: N04 | Requirements: N04.FR.01, N04.FR.02, N04.FR.17
N04.FR.01: When the Charging Station receives a SetVariableMonitoringRequest with an X number of SetMonitoringData elements The Charging Station SHALL respond with an SetVariableMonitoringResponse with an equal (X) number of SetMonitoringResult elements, one for every SetMonitoringData element in the SetVariableMonitoringRequest.
    Precondition: When the Charging Station receives a SetVariableMonitoringRequest with an X number of SetMonitoringData elements
N04.FR.02: Every SetMonitoringResult element in the SetVariableMonitoringResponse SHALL contain the same component and variable combination as one of the SetMonitoringData elements in the SetVariableMonitoringRequest.
    Precondition: N04.FR.01
N04.FR.17: When the CSMS sends a SetVariableMonitoringRequest with type Delta for a Variable that is NOT of a numeric type It is RECOMMENDED to use a value of 1. value is irrelevant for non-numeric types (e.g. any type except decimal or integer), since the monitor is triggered by
    Precondition: When the CSMS sends a SetVariableMonitoringRequest with type Delta for a Variable that is NOT of a numeric type
System under test: CSMS

Description:
    CSMS sends a request to activate monitoring on one variable.

Purpose:
    To test that CSMS supports setting monitoring on one variable.

Prerequisites:
    Component "EVSE", evse <Configured evseId>, variable "AvailabilityState", monitor type Delta

Main:
    1. CSMS sends SetVariableMonitoringRequest with:
       - setMonitoringData[0].value = 1
       - setMonitoringData[0].type = Delta
       - setMonitoringData[0].severity = 8
       - setMonitoringData[0].component.name = "EVSE"
       - setMonitoringData[0].component.evse.id = <Configured evseId>
       - setMonitoringData[0].variable.name = "AvailabilityState"
    2. OCTT responds SetVariableMonitoringResponse with setMonitoringResult[0].status = Accepted

Tool validations:
    * Step 1: setMonitoringData fields as listed above

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
    MonitorEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_n_08():
    """Set Variable Monitoring - One SetMonitoringData element."""
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

    # Step 1: Wait for CSMS to send SetVariableMonitoringRequest
    await asyncio.wait_for(
        cp._received_set_variable_monitoring.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate request content
    assert cp._set_variable_monitoring_data is not None
    assert len(cp._set_variable_monitoring_data) >= 1, \
        "Expected at least 1 setMonitoringData element"

    item = cp._set_variable_monitoring_data[0]

    # Tool validation: value = 1
    assert item.get('value') == 1, \
        f"Expected setMonitoringData[0].value=1, got {item.get('value')}"

    # Tool validation: type = Delta
    assert item.get('type') == MonitorEnumType.delta, \
        f"Expected setMonitoringData[0].type=Delta, got {item.get('type')}"

    # Tool validation: severity = 8
    assert item.get('severity') == 8, \
        f"Expected setMonitoringData[0].severity=8, got {item.get('severity')}"

    # Tool validation: component.name = "EVSE"
    component = item.get('component', {})
    assert component.get('name') == 'EVSE', \
        f"Expected setMonitoringData[0].component.name='EVSE', got {component.get('name')}"

    # Tool validation: component.evse.id = <Configured evseId>
    evse = component.get('evse', {})
    assert evse.get('id') == CONFIGURED_EVSE_ID, \
        f"Expected setMonitoringData[0].component.evse.id={CONFIGURED_EVSE_ID}, got {evse.get('id')}"

    # Tool validation: variable.name = "AvailabilityState"
    variable = item.get('variable', {})
    assert variable.get('name') == 'AvailabilityState', \
        f"Expected setMonitoringData[0].variable.name='AvailabilityState', got {variable.get('name')}"

    logging.info("TC_N_08 completed successfully")
    start_task.cancel()
    await ws.close()
