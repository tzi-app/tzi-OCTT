"""
TC_L_23 - Unpublish Firmware - Download Ongoing
Use case: L04 | Requirements: N/a
System under test: CSMS

Description:
    This test case covers the unpublish firmware process where the CSMS sends an
    UnpublishFirmwareRequest and the Charging Station responds that a download is still
    ongoing and cannot unpublish yet.

Purpose:
    To verify if the CSMS is able to send an UnpublishFirmwareRequest and correctly handle the
    DownloadOngoing response from the Charging Station.

Main:
    1. CSMS sends UnpublishFirmwareRequest
    2. CS responds with UnpublishFirmwareResponse (status=DownloadOngoing)

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
    UnpublishFirmwareStatusEnumType,
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
async def test_tc_l_23():
    """Unpublish Firmware - Download Ongoing."""
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
    # Configure CS to respond with DownloadOngoing
    cp._unpublish_firmware_response_status = UnpublishFirmwareStatusEnumType.download_ongoing
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1-2: Wait for CSMS to send UnpublishFirmwareRequest
    await asyncio.wait_for(
        cp._received_unpublish_firmware.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate UnpublishFirmwareRequest was received
    assert cp._unpublish_firmware_data is not None
    assert cp._unpublish_firmware_data['checksum'] is not None, \
        "UnpublishFirmwareRequest.checksum must be present"

    # CS responded with DownloadOngoing (configured before start)
    logging.info(f"CS responded with DownloadOngoing for checksum: {cp._unpublish_firmware_data['checksum']}")

    logging.info("TC_L_23 completed successfully")
    start_task.cancel()
    await ws.close()
