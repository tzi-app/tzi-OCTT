"""
TC_L_17 - Publish Firmware - Published
Use case: L03 | Requirements: N/a
System under test: CSMS

Description:
    This test case covers the publish firmware process where the Charging Station successfully
    downloads, verifies the checksum, and publishes the firmware for other stations to download.

Purpose:
    To verify if the CSMS is able to send a PublishFirmwareRequest and correctly handle the
    PublishFirmwareStatusNotification progression through to Published status with a local location.

Main:
    1. CSMS sends PublishFirmwareRequest (with location configured)
    2. CS responds with PublishFirmwareResponse (status=Accepted)
    3. CS sends PublishFirmwareStatusNotification progression:
       Downloading -> Downloaded -> ChecksumVerified -> Published (with location)

Tool validations:
    * Step 1: PublishFirmwareRequest
      - location is configured (present)

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
from utils import get_basic_auth_headers, build_default_ssl_context
from trigger import send_call

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_l_17():
    """Publish Firmware - Published."""
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

    # Step 1-2: Trigger CSMS to send PublishFirmwareRequest
    async def trigger_publish_firmware():
        await asyncio.sleep(1)
        await send_call(cp_id, "PublishFirmware", {
            "location": "https://example.com/firmware-v2.0.bin",
            "checksum": "abc123def456",
            "requestId": 1,
        })
    trigger_task = asyncio.create_task(trigger_publish_firmware())
    await asyncio.wait_for(
        cp._received_publish_firmware.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    # Validate PublishFirmwareRequest content
    assert cp._publish_firmware_data is not None
    req_data = cp._publish_firmware_data

    # Tool validation Step 1: location is configured
    assert req_data['location'] is not None and req_data['location'] != '', \
        "PublishFirmwareRequest.location must be configured"
    logging.info(f"PublishFirmwareRequest location: {req_data['location']}")

    request_id = req_data['request_id']

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

    # PublishFirmwareStatusNotification - ChecksumVerified
    resp = await cp.send_publish_firmware_status_notification_request(
        status=PublishFirmwareStatusEnumType.checksum_verified,
        request_id=request_id,
    )
    assert resp is not None

    # PublishFirmwareStatusNotification - Published (with local location)
    local_firmware_uri = f'https://{cp_id}.local/firmware/published_firmware.bin'
    resp = await cp.send_publish_firmware_status_notification_request(
        status=PublishFirmwareStatusEnumType.published,
        location=[local_firmware_uri],
        request_id=request_id,
    )
    assert resp is not None

    logging.info("TC_L_17 completed successfully")
    start_task.cancel()
    await ws.close()
