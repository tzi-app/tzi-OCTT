"""
TC_L_06 - Secure Firmware Update - InvalidSignature
Use case: L01 | Requirements: L01.FR.01, L01.FR.11
L01.FR.01: Whenever the Charging Station enters a new state in the firmware update process, the Charging Station SHALL send a FirmwareStatusNotificationRequest message to the CSMS with this new status.
    Precondition: Whenever the Charging Station enters a new state in the firmware update process.
L01.FR.11: For security purposes the CSMS SHALL include the Firmware Signing certificate in the UpdateFirmwareRequest.
System under test: CSMS

Description:
    This test case covers the secure firmware update process where the Charging Station accepts the
    update request and starts downloading, but after download detects that the firmware signature is
    invalid.

Purpose:
    To verify if the CSMS correctly handles InvalidSignature firmware status and accepts the
    SecurityEventNotification for InvalidFirmwareSignature.

Main:
    1. CSMS sends UpdateFirmwareRequest
    2. CS responds with UpdateFirmwareResponse (status=Accepted)
    3. CS sends FirmwareStatusNotification: Downloading -> Downloaded -> InvalidSignature
    4. CS sends SecurityEventNotificationRequest (type=InvalidFirmwareSignature)
    5. CSMS responds with SecurityEventNotificationResponse

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
    FirmwareStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context
from trigger import send_call

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_l_06():
    """Secure Firmware Update - InvalidSignature."""
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

    # Step 1-2: Trigger CSMS to send UpdateFirmwareRequest
    async def trigger_update_firmware():
        await asyncio.sleep(1)
        await send_call(cp_id, "UpdateFirmware", {
            "requestId": 1,
            "firmware": {
                "location": "https://example.com/firmware-v2.0.bin",
                "retrieveDateTime": now_iso(),
                "signingCertificate": "MIICaTCCAdKgAwIBAgIUXzo...",
                "signature": "MEUCIQC7p...",
            },
        })
    trigger_task = asyncio.create_task(trigger_update_firmware())
    await asyncio.wait_for(
        cp._received_update_firmware.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    assert cp._update_firmware_data is not None

    # CS responded with Accepted (default handler behavior)

    # FirmwareStatusNotification - Downloading
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.downloading
    )
    assert resp is not None

    # FirmwareStatusNotification - Downloaded
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.downloaded
    )
    assert resp is not None

    # FirmwareStatusNotification - InvalidSignature
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.invalid_signature
    )
    assert resp is not None

    # CS sends SecurityEventNotification
    resp = await cp.send_security_event_notification(
        event_type='InvalidFirmwareSignature',
        timestamp=now_iso(),
    )
    assert resp is not None

    logging.info("TC_L_06 completed successfully")
    start_task.cancel()
    await ws.close()
