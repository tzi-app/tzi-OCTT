"""
TC_L_10 - Secure Firmware Update - AcceptedCanceled
Use case: L01 | Requirements: L01.FR.01, L01.FR.11, L01.FR.24
L01.FR.01: Whenever the Charging Station enters a new state in the firmware update process, the Charging Station SHALL send a FirmwareStatusNotificationRequest message to the CSMS with this new status.
    Precondition: Whenever the Charging Station enters a new state in the firmware update process.
L01.FR.11: For security purposes the CSMS SHALL include the Firmware Signing certificate in the UpdateFirmwareRequest.
L01.FR.24: When a Charging Station is installing new Firmware OR is going to install new Firmware, but has received an UpdateFirmware command to install it at a later time AND the Charging Station receives a new UpdateFirmwareRequest, the Charging Station SHOULD cancel the ongoing firmware update AND respond with status AcceptedCanceled.
    Precondition: When a Charging Station is installing new Firmware OR is going to install new Firmware, but has received an UpdateFirmware command to install it at a later time AND the Charging Station receives a new UpdateFirmwareRequest
System under test: CSMS

Description:
    This test case covers the scenario where a firmware update is already in progress (downloading),
    and the CSMS sends a second UpdateFirmwareRequest. The Charging Station cancels the first update
    (AcceptedCanceled) and proceeds with the new one through to successful installation.

Purpose:
    To verify if the CSMS can handle the AcceptedCanceled status when sending a new firmware update
    while one is already in progress.

Main:
    1. CSMS sends first UpdateFirmwareRequest
    2. CS responds Accepted, starts Downloading
    3. CSMS sends second UpdateFirmwareRequest
    4. CS responds AcceptedCanceled (first canceled, second accepted)
    5. CS continues with new firmware: Downloading -> Downloaded -> SignatureVerified ->
       Installing -> InstallRebooting -> Boot -> Status -> Installed

Tool validations:
    * Step 18: BootNotificationResponse
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

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.routing import on
from ocpp.v201 import call_result
from ocpp.v201.enums import (
    Action,
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    FirmwareStatusEnumType,
    UpdateFirmwareStatusEnumType,
    EventTriggerEnumType,
    EventNotificationEnumType,
)

from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context
from trigger import send_call

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


class FirmwareCancelMockCP(TziChargePoint):
    """MockChargePoint that tracks multiple UpdateFirmwareRequests and responds AcceptedCanceled on the second."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_firmware_count = 0
        self._received_second_update_firmware = asyncio.Event()
        self._second_update_firmware_data = None

    @on(Action.update_firmware)
    async def on_update_firmware(self, request_id, firmware, retries=None, retry_interval=None, **kwargs):
        self._update_firmware_count += 1
        logging.info(f"Received UpdateFirmwareRequest #{self._update_firmware_count}: request_id={request_id}")

        if self._update_firmware_count == 1:
            # First request - accept it
            self._update_firmware_data = {
                'request_id': request_id,
                'firmware': firmware,
                'retries': retries,
                'retry_interval': retry_interval,
            }
            self._received_update_firmware.set()
            return call_result.UpdateFirmware(
                status=UpdateFirmwareStatusEnumType.accepted
            )
        else:
            # Second request - accept and cancel the first
            self._second_update_firmware_data = {
                'request_id': request_id,
                'firmware': firmware,
                'retries': retries,
                'retry_interval': retry_interval,
            }
            self._received_second_update_firmware.set()
            return call_result.UpdateFirmware(
                status=UpdateFirmwareStatusEnumType.accepted_canceled
            )


@pytest.mark.asyncio
async def test_tc_l_10():
    """Secure Firmware Update - AcceptedCanceled."""
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

    cp = FirmwareCancelMockCP(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1-2: Trigger first UpdateFirmwareRequest
    async def trigger_first():
        await asyncio.sleep(1)
        await send_call(cp_id, "UpdateFirmware", {
            "requestId": 1,
            "firmware": {
                "location": "https://example.com/firmware-v1.0.bin",
                "retrieveDateTime": now_iso(),
                "signingCertificate": "MIICaTCCAdKgAwIBAgIUXzo...",
                "signature": "MEUCIQC7p...",
            },
        })
    trigger_task1 = asyncio.create_task(trigger_first())
    await asyncio.wait_for(
        cp._received_update_firmware.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task1.cancel()
    assert cp._update_firmware_data is not None

    # Step 3: First firmware starts downloading
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.downloading
    )
    assert resp is not None

    # Step 5-6: Trigger second UpdateFirmwareRequest
    async def trigger_second():
        await asyncio.sleep(1)
        await send_call(cp_id, "UpdateFirmware", {
            "requestId": 2,
            "firmware": {
                "location": "https://example.com/firmware-v2.0.bin",
                "retrieveDateTime": now_iso(),
                "signingCertificate": "MIICaTCCAdKgAwIBAgIUXzo...",
                "signature": "MEUCIQC7p...",
            },
        })
    trigger_task2 = asyncio.create_task(trigger_second())
    await asyncio.wait_for(
        cp._received_second_update_firmware.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task2.cancel()
    assert cp._second_update_firmware_data is not None

    # CS responded with AcceptedCanceled (first canceled, second accepted)

    # Step 7: New firmware starts downloading
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.downloading
    )
    assert resp is not None

    # Step 9: Downloaded
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.downloaded
    )
    assert resp is not None

    # Step 11: SignatureVerified
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.signature_verified
    )
    assert resp is not None

    # Step 13: Installing
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.installing
    )
    assert resp is not None

    # Step 15: InstallRebooting
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.install_rebooting
    )
    assert resp is not None

    # Step 17-18: BootNotification with FirmwareUpdate reason
    boot_response = await cp.send_boot_notification_with_reason('FirmwareUpdate')
    assert boot_response.status == RegistrationStatusEnumType.accepted, \
        f"Expected BootNotificationResponse status=Accepted, got {boot_response.status}"

    # Step 19: StatusNotification - Available + NotifyEvent
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

    # Step 21: FirmwareStatusNotification - Installed
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.installed
    )
    assert resp is not None

    logging.info("TC_L_10 completed successfully")
    start_task.cancel()
    await ws.close()
