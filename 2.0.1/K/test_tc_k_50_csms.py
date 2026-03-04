"""
TC_K_50 - Reset / release external charging limit - Without ongoing transaction
Use case: K13 | Requirements: N/a
System under test: CSMS

Description:
    A charging schedule or charging limit can be removed by an external system on the Charging Station. An
    external control system sends a signal to release a previously imposed charging limit to a Charging
    Station. The Charging Station notifies the CSMS about this.

Purpose:
    To verify if the CSMS is able to receive the notify from a charging station and respond correctly as
    described at the OCPP specification.

Main:
    1. The OCTT sends a ClearedChargingLimitRequest with chargingLimitSource EMS
    2. The CSMS responds with a ClearedChargingLimitResponse
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201 import call
from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    ChargingLimitSourceEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_k_50():
    """Reset / release external charging limit - Without ongoing transaction."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
    ws = await websockets.connect(uri=uri, subprotocols=['ocpp2.0.1'], extra_headers=headers)
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted
    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1: Send ClearedChargingLimitRequest
    payload = call.ClearedChargingLimit(
        charging_limit_source=ChargingLimitSourceEnumType.ems,
    )
    # Step 2: CSMS responds with ClearedChargingLimitResponse
    response = await cp.call(payload)
    assert response is not None

    logging.info("TC_K_50 completed successfully")
    start_task.cancel()
    await ws.close()
