"""
TC_L_19 - Publish Firmware - Invalid Checksum
Use case: L03 | Requirements: N/a
System under test: CSMS

Description:
    This test case covers the publish firmware process where the Charging Station downloads the
    firmware but detects an invalid checksum.

Purpose:
    To verify if the CSMS correctly handles an InvalidChecksum publish firmware status notification
    from the Charging Station.

Main:
    1. CSMS sends PublishFirmwareRequest
    2. CS responds with PublishFirmwareResponse (status=Accepted)
    3. CS sends PublishFirmwareStatusNotification progression:
       Downloading -> Downloaded -> InvalidChecksum

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
    PublishFirmwareStatusEnumType,
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
async def test_tc_l_19():
    """Publish Firmware - Invalid Checksum."""
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

    # Step 1-2: Wait for CSMS to send PublishFirmwareRequest
    await asyncio.wait_for(
        cp._received_publish_firmware.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._publish_firmware_data is not None
    request_id = cp._publish_firmware_data['request_id']

    # CS responded with Accepted (handled by on_publish_firmware handler)

    # PublishFirmwareStatusNotification - Downloading
    resp = await cp.send_publish_firmware_status_notification_request(
        status=PublishFirmwareStatusEnumType.downloading,
        request_id=request_id,
    )
    assert resp is not None

    # PublishFirmwareStatusNotification - Downloaded
    resp = await cp.send_publish_firmware_status_notification_request(
        status=PublishFirmwareStatusEnumType.downloaded,
        request_id=request_id,
    )
    assert resp is not None

    # PublishFirmwareStatusNotification - InvalidChecksum
    resp = await cp.send_publish_firmware_status_notification_request(
        status=PublishFirmwareStatusEnumType.invalid_checksum,
        request_id=request_id,
    )
    assert resp is not None

    logging.info("TC_L_19 completed successfully")
    start_task.cancel()
    await ws.close()
