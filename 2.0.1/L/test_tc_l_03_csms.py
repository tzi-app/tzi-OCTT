"""
TC_L_03 - Secure Firmware Update - DownloadScheduled
Use case: L01 | Requirements: L01.FR.01, L01.FR.11, L01.FR.15
L01.FR.01: Whenever the Charging Station enters a new state in the firmware update process, the Charging Station SHALL send a FirmwareStatusNotificationRequest message to the CSMS with this new status.
    Precondition: Whenever the Charging Station enters a new state in the firmware update process.
L01.FR.11: For security purposes the CSMS SHALL include the Firmware Signing certificate in the UpdateFirmwareRequest.
L01.FR.15: When a Charging Station needs to reboot before installing the downloaded firmware, the Charging Station SHALL send a FirmwareStatusNotificationRequest with status InstallRebooting, before rebooting.
    Precondition: When a Charging Station needs to reboot before installing the downloaded firmware.
System under test: CSMS

Description:
    This test case covers the secure firmware update process where the retrieveDateTime is in the future.
    The Charging Station reports DownloadScheduled status while waiting for the retrieveDateTime before
    starting the download.

Purpose:
    To verify if the CSMS handles a firmware update with a scheduled retrieve time, where the CS reports
    DownloadScheduled status while waiting for the retrieveDateTime.

Main:
    1. CSMS sends UpdateFirmwareRequest with firmware.retrieveDateTime in the future
    2. CS responds Accepted
    3. CS sends FirmwareStatusNotification progression:
       DownloadScheduled -> Downloading -> Downloaded -> SignatureVerified -> Installing ->
       InstallRebooting -> BootNotification(FirmwareUpdate) -> StatusNotification -> Installed

Tool validations:
    * Step 1: UpdateFirmwareRequest
      - firmware.retrieveDateTime is in the future
    * Step 16: BootNotificationResponse
      - status = Accepted

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
from datetime import datetime

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    FirmwareStatusEnumType,
    EventTriggerEnumType,
    EventNotificationEnumType,
)
from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context
from trigger import send_call
from datetime import timedelta, timezone

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_l_03():
    """Secure Firmware Update - DownloadScheduled."""
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

    # Step 1-2: Trigger CSMS to send UpdateFirmwareRequest with future retrieveDateTime
    future_retrieve = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    async def trigger_update_firmware():
        await asyncio.sleep(1)
        await send_call(cp_id, "UpdateFirmware", {
            "requestId": 1,
            "firmware": {
                "location": "https://example.com/firmware-v2.0.bin",
                "retrieveDateTime": future_retrieve,
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

    # Validate UpdateFirmwareRequest content
    assert cp._update_firmware_data is not None
    firmware = cp._update_firmware_data['firmware']

    # Tool validation Step 1: firmware.retrieveDateTime should be in the future
    retrieve_dt = firmware.get('retrieve_date_time') or firmware.get('retrieveDateTime')
    assert retrieve_dt is not None, \
        "firmware.retrieveDateTime must be present in UpdateFirmwareRequest"
    retrieve_dt_parsed = datetime.fromisoformat(retrieve_dt.replace('Z', '+00:00'))
    assert retrieve_dt_parsed > datetime.now(retrieve_dt_parsed.tzinfo), \
        f"firmware.retrieveDateTime must be in the future, got {retrieve_dt}"
    logging.info(f"firmware.retrieveDateTime = {retrieve_dt} (validated as future)")

    # CS responded with Accepted (handled by on_update_firmware handler)

    # FirmwareStatusNotification - DownloadScheduled (waiting for retrieveDateTime)
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.download_scheduled
    )
    assert resp is not None

    # Simulate waiting for retrieveDateTime
    await asyncio.sleep(1)

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

    # FirmwareStatusNotification - SignatureVerified
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.signature_verified
    )
    assert resp is not None

    # FirmwareStatusNotification - Installing
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.installing
    )
    assert resp is not None

    # FirmwareStatusNotification - InstallRebooting
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.install_rebooting
    )
    assert resp is not None

    # BootNotification with FirmwareUpdate reason
    boot_response = await cp.send_boot_notification_with_reason('FirmwareUpdate')
    assert boot_response.status == RegistrationStatusEnumType.accepted, \
        f"Expected BootNotificationResponse status=Accepted, got {boot_response.status}"

    # StatusNotification - Available + NotifyEvent
    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    event_data = [
        EventDataType(
            trigger=EventTriggerEnumType.delta,
            actual_value='Available',
            component=ComponentType(name='Connector', evse={"id": EVSE_ID}),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=EVSE_ID,
            event_notification_type=EventNotificationEnumType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)

    # FirmwareStatusNotification - Installed
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.installed
    )
    assert resp is not None

    logging.info("TC_L_03 completed successfully")
    start_task.cancel()
    await ws.close()
