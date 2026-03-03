"""
Test case name      Reset Charging Station - With Ongoing Transaction - Immediate
Test case Id        TC_B_22_CSMS
Use case Id(s)      B12
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers how the CSMS can remotely request the Charging Station to reset itself
                    by sending a ResetRequest during a transaction. When ResetRequest "Immediate" is sent the
                    charging stations will try to stop all transactions before rebooting.
Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP specification.

Prerequisite(s)     n/a

Before (Reusable State): EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to reboot the Charging Station with status Immediate
1. The CSMS sends a ResetRequest with status Immediate
2. The OCTT responds with a ResetResponse with status Accepted
3. The OCTT sends a TransactionEventRequest (Ended, ResetCommand, ImmediateReset)
4. The CSMS responds with a TransactionEventResponse
5. The OCTT sends a BootNotificationRequest with reason RemoteReset
6. The CSMS responds with a BootNotificationResponse
7. The OCTT notifies the CSMS about the current state of all connectors.
8. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: ResetRequest
    - type Immediate
    - evseId must be omitted
* Step 6:
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
from ocpp.v201.call import TransactionEvent

from tzi_charge_point import TziChargePoint
from trigger import reset
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']


@pytest.mark.asyncio
async def test_tc_b_22():
    """Reset CS - With Ongoing Transaction - Immediate: immediate reset stops transaction."""
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

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Simulate EnergyTransferStarted - start a transaction
    transaction_id = generate_transaction_id()

    started_event = TransactionEvent(
        event_type='Started',
        timestamp=now_iso(),
        trigger_reason='CablePluggedIn',
        seq_no=0,
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': 'EVConnected',
        },
        evse={'id': CONFIGURED_EVSE_ID, 'connector_id': CONFIGURED_CONNECTOR_ID},
        id_token={'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
    )
    await cp.send_transaction_event_request(started_event)

    # Step 1-2: Trigger CSMS to send ResetRequest with type Immediate
    trigger_task = asyncio.create_task(reset(BASIC_AUTH_CP, "Immediate"))

    await asyncio.wait_for(
        cp._received_reset.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task

    assert cp._reset_data is not None
    assert cp._reset_data['type'] == 'Immediate', \
        f"Expected Immediate reset type, got: {cp._reset_data['type']}"
    # Tool validation: evseId must be omitted for Charging Station reset
    assert cp._reset_data['evse_id'] is None, \
        f"Expected evseId to be omitted, got: {cp._reset_data['evse_id']}"

    # Step 3-4: Send TransactionEventRequest (Ended, ResetCommand, ImmediateReset)
    ended_event = TransactionEvent(
        event_type='Ended',
        timestamp=now_iso(),
        trigger_reason='ResetCommand',
        seq_no=1,
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': 'EVConnected',
            'stopped_reason': 'ImmediateReset',
        },
    )
    await cp.send_transaction_event_request(ended_event)

    # Close connection to simulate reset
    start_task.cancel()
    await ws.close()

    # Step 5-6: Reconnect with RemoteReset reason
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification_with_reason('RemoteReset')
    assert boot_response is not None
    assert boot_response.status == RegistrationStatusEnumType.accepted

    # Step 7-8: Notify CSMS about connector states
    # Configured connectorId shows Occupied (still plugged in), others Available
    await cp.send_status_notification(CONFIGURED_CONNECTOR_ID, ConnectorStatusEnumType.occupied)
    await cp.send_notify_event([{
        'event_id': 1,
        'timestamp': '2024-01-01T00:00:00Z',
        'trigger': 'Delta',
        'actual_value': 'Occupied',
        'event_notification_type': 'HardWiredNotification',
        'component': {'name': 'Connector'},
        'variable': {'name': 'AvailabilityState'},
    }])

    start_task.cancel()
    await ws.close()
