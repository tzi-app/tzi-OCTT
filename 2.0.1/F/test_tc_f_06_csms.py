"""
TC_F_06 - Remote unlock Connector - Without ongoing transaction - Accepted
Use case: F05 | Requirements: n/a
System under test: CSMS

Description:
    This test case describes how the CSMS can be requested to send an UnlockConnectorRequest to the
    charging station. It sometimes happens that a connector of a Charging Station socket does not unlock
    correctly. This happens most of the time when there is tension on the charging cable. This means the
    driver cannot unplug his charging cable from the Charging Station. To help a driver, the CSO can send
    a UnlockConnectorRequest to the Charging Station. The Charging Station will then try to unlock the
    connector again.

Purpose:
    To verify if the CSMS is able to perform the remote unlock connector mechanism as described at the
    OCPP specification.

Main:
    1. CSMS sends UnlockConnectorRequest (evseId=<configured>, connectorId=<configured>)
    2. CS responds with UnlockConnectorResponse (status=Unlocked)

Tool validations:
    * Step 1: UnlockConnectorRequest
      - evseId <Configured evseId>
      - connectorId <Configured connectorId>

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
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
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_f_06():
    """Remote unlock Connector - Without ongoing transaction - Accepted."""
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

    await cp.send_status_notification(1, ConnectorStatusEnumType.available, evse_id=EVSE_ID)

    # Step 1-2: Trigger CSMS to send UnlockConnectorRequest
    async def trigger_unlock():
        await asyncio.sleep(1)
        await send_call(BASIC_AUTH_CP, "UnlockConnector", {
            "evseId": EVSE_ID,
            "connectorId": CONNECTOR_ID,
        })

    trigger_task = asyncio.create_task(trigger_unlock())

    await asyncio.wait_for(
        cp._received_unlock_connector.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    # Validate Step 1: UnlockConnectorRequest content
    assert cp._unlock_connector_data is not None
    assert cp._unlock_connector_data['evse_id'] == EVSE_ID, \
        f"Expected evseId={EVSE_ID}, got {cp._unlock_connector_data['evse_id']}"
    assert cp._unlock_connector_data['connector_id'] == CONNECTOR_ID, \
        f"Expected connectorId={CONNECTOR_ID}, got {cp._unlock_connector_data['connector_id']}"

    logging.info("TC_F_06 completed successfully")
    start_task.cancel()
    await ws.close()
