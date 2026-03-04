"""
TC_L_09 - Secure Firmware Update - InstallationFailed
Use case: L01 | Requirements: L01.FR.01, L01.FR.11
L01.FR.01: Whenever the Charging Station enters a new state in the firmware update process, the Charging Station SHALL send a FirmwareStatusNotificationRequest message to the CSMS with this new status.
    Precondition: Whenever the Charging Station enters a new state in the firmware update process.
L01.FR.11: For security purposes the CSMS SHALL include the Firmware Signing certificate in the UpdateFirmwareRequest.
System under test: CSMS

Description:
    This test case covers the secure firmware update process where the Charging Station goes through
    the full firmware update lifecycle including reboot, but the installation ultimately fails.

Purpose:
    To verify if the CSMS correctly handles an InstallationFailed firmware status notification after
    the Charging Station reboots.

Main:
    1. CSMS sends UpdateFirmwareRequest
    2. CS responds with UpdateFirmwareResponse (status=Accepted)
    3. CS sends FirmwareStatusNotification progression:
       Downloading -> Downloaded -> SignatureVerified -> Installing -> InstallRebooting
    4. CS sends BootNotification(FirmwareUpdate)
    5. CS sends StatusNotification(Available)
    6. CS sends FirmwareStatusNotification(InstallationFailed)

Tool validations:
    * Step 14: BootNotificationResponse
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

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_l_09():
    """Secure Firmware Update - InstallationFailed."""
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

    # Step 1-2: Wait for CSMS to send UpdateFirmwareRequest
    await asyncio.wait_for(
        cp._received_update_firmware.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

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

    # FirmwareStatusNotification - InstallationFailed
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.installation_failed
    )
    assert resp is not None

    logging.info("TC_L_09 completed successfully")
    start_task.cancel()
    await ws.close()
