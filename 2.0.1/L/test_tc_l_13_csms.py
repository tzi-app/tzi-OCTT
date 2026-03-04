"""
TC_L_13 - Secure Firmware Update - Ongoing transaction, AllowNewSessionsPendingFirmwareUpdate=false
Use case: L01 | Requirements: L01.FR.01, L01.FR.11
L01.FR.01: Whenever the Charging Station enters a new state in the firmware update process, the Charging Station SHALL send a FirmwareStatusNotificationRequest message to the CSMS with this new status.
    Precondition: Whenever the Charging Station enters a new state in the firmware update process.
L01.FR.11: For security purposes the CSMS SHALL include the Firmware Signing certificate in the UpdateFirmwareRequest.
System under test: CSMS

Description:
    This test case covers the secure firmware update process where there is an ongoing transaction.
    The Charging Station first reports DownloadScheduled, then makes the EVSE unavailable, waits for
    the transaction to complete (StopAuthorized, EVConnectedPostSession, EVDisconnected), and then
    proceeds with the firmware update lifecycle through to successful installation.

Purpose:
    To verify if the CSMS correctly handles a firmware update that arrives during an ongoing
    transaction, with the CS properly transitioning to unavailable and completing the transaction
    before proceeding with the firmware update.

Before:
    State is EnergyTransferStarted

Main:
    1. CSMS sends UpdateFirmwareRequest
    2. CS responds Accepted
    3. CS sends FirmwareStatusNotification(DownloadScheduled)
    4. CS sends StatusNotification(Unavailable) and NotifyEvent(Unavailable)
    5. Execute StopAuthorized, EVConnectedPostSession, EVDisconnected
    6. CS sends FirmwareStatusNotification progression:
       Downloading -> Downloaded -> SignatureVerified -> Installing -> InstallRebooting
    7. CS sends BootNotification(FirmwareUpdate)
    8. CS sends StatusNotification(Available)
    9. CS sends FirmwareStatusNotification(Installed)

Tool validations:
    * Step 1: UpdateFirmwareRequest
      - firmware.signingCertificate is present
    * Step 19: BootNotificationResponse
      - status = Accepted

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
    VALID_ID_TOKEN            - Valid idToken value
    VALID_ID_TOKEN_TYPE       - Valid idToken type
    TRANSACTION_DURATION      - Duration of simulated transaction in seconds (default 5)
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
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.stop_authorized import stop_authorized
from reusable_states.ev_connected_post_session import ev_connected_post_session
from reusable_states.ev_disconnected import ev_disconnected

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


@pytest.mark.asyncio
async def test_tc_l_13():
    """Secure Firmware Update - Ongoing transaction."""
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

    transaction_id = generate_transaction_id()

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Before: Execute Reusable State EnergyTransferStarted
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Step 1-2: Wait for CSMS to send UpdateFirmwareRequest
    await asyncio.wait_for(
        cp._received_update_firmware.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate UpdateFirmwareRequest content
    assert cp._update_firmware_data is not None
    firmware = cp._update_firmware_data['firmware']

    # Tool validation Step 1: firmware.signingCertificate must be present
    assert firmware.get('signing_certificate') or firmware.get('signingCertificate'), \
        "firmware.signingCertificate must be present in UpdateFirmwareRequest"

    # CS responded with Accepted (default handler behavior)

    # Step 3: FirmwareStatusNotification - DownloadScheduled
    resp = await cp.send_firmware_status_notification_request(
        FirmwareStatusEnumType.download_scheduled
    )
    assert resp is not None

    # Step 5: CS sends StatusNotification(Unavailable)
    await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusEnumType.unavailable,
    )

    # Step 7: CS sends NotifyEvent(Unavailable)
    event_data = [
        EventDataType(
            trigger=EventTriggerEnumType.delta,
            actual_value='Unavailable',
            component=ComponentType(name='Connector', evse={"id": EVSE_ID}),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=EVSE_ID,
            event_notification_type=EventNotificationEnumType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)

    # Wait for transaction duration
    await asyncio.sleep(TRANSACTION_DURATION)

    # Execute StopAuthorized
    await stop_authorized(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                          transaction_id=transaction_id)

    # Execute EVConnectedPostSession
    await ev_connected_post_session(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                    transaction_id=transaction_id)

    # Execute EVDisconnected
    await ev_disconnected(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                          transaction_id=transaction_id)

    # Now proceed with firmware update
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

    logging.info("TC_L_13 completed successfully")
    start_task.cancel()
    await ws.close()
