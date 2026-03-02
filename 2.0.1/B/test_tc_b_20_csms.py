"""
Test case name      Reset Charging Station - Without ongoing transaction - OnIdle
Test case Id        TC_B_20_CSMS
Use case Id(s)      B11
Requirement(s)      B11.FR.04

Requirement Details:
    B11.FR.04: The Charging Station SHALL send a NotifyReportRequest for each component-variable combination that changed.
        Precondition: B11.FR.03
System under test   CSMS

Description         This test case covers how the CSMS can request the Charging Station to reset itself by sending
                    a ResetRequest without any ongoing transaction. This could for example be necessary if the
                    Charging Station is not functioning correctly.
Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP specification.

Prerequisite(s)     n/a

Test Scenario
Manual Action: Request the CSMS to reboot the Charging Station with type OnIdle
1. The CSMS sends a ResetRequest
2. The OCTT responds with a ResetResponse with status Accepted
3. The OCTT sends a BootNotificationRequest
4. The CSMS responds with a BootNotificationResponse
5. The OCTT notifies the CSMS about the current state of all connectors.
6. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: ResetRequest
    - evseId must be omitted
* Step 4:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    - N/a
"""

import asyncio
import pytest
import os
import time
import logging

import websockets
from ocpp.v201.enums import (
    RegistrationStatusEnumType, ConnectorStatusEnumType, ResetStatusEnumType
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP_B']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_b_20():
    """Reset CS - Without ongoing transaction - OnIdle."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)
    ssl_ctx = build_default_ssl_context() if uri.startswith('wss://') else None

    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    cp._reset_response_status = ResetStatusEnumType.accepted
    start_task = asyncio.create_task(cp.start())

    # Boot to establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Step 1-2: Wait for CSMS to send ResetRequest
    await asyncio.wait_for(
        cp._received_reset.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._reset_data is not None
    reset_type = cp._reset_data['type']
    assert reset_type == 'OnIdle', \
        f"Expected OnIdle reset type, got: {reset_type}"
    # Tool validation: evseId must be omitted for Charging Station reset
    assert cp._reset_data['evse_id'] is None, \
        f"Expected evseId to be omitted, got: {cp._reset_data['evse_id']}"
    logging.info(f"Received ResetRequest: type={reset_type}")

    # Close current connection to simulate reset
    start_task.cancel()
    await ws.close()

    # Step 3-4: Reconnect after reset
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification()
    assert boot_response is not None
    assert boot_response.status == RegistrationStatusEnumType.accepted

    # Step 5-6: Notify CSMS about connector states
    await cp.send_status_notification(1, ConnectorStatusEnumType.available)
    await cp.send_notify_event([{
        'event_id': 1,
        'timestamp': '2024-01-01T00:00:00Z',
        'trigger': 'Delta',
        'actual_value': 'Available',
        'event_notification_type': 'HardWiredNotification',
        'component': {'name': 'Connector'},
        'variable': {'name': 'AvailabilityState'},
    }])

    start_task.cancel()
    await ws.close()
