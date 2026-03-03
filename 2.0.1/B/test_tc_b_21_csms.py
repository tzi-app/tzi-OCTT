"""
Test case name      Reset Charging Station - With Ongoing Transaction - OnIdle
Test case Id        TC_B_21_CSMS
Use case Id(s)      B12
Requirement(s)      B12.FR.01, B12.FR.03, E07.FR.03

Requirement Details:
    B12.FR.01: When the Charging Station receives a ResetRequest(OnIdle) AND a transaction is ongoing The Charging Station SHALL respond with a ResetResponse(Scheduled), to indicate whether the Charging Station will attempt to reset itself or EVSE after all transactions on Charging Station or EVSE have ended.
        Precondition: When the Charging Station receives a ResetRequest(OnIdle) AND a transaction is ongoing
    B12.FR.03: If no evseId is supplied AND If any transaction is in progress and an OnIdle reset is received. The transaction of the Charging Station SHALL be terminated normally, before the reboot, e.g. as in E06 - Stop Transaction.
        Precondition: If no evseId is supplied AND If any transaction is in progress and an OnIdle reset is received.
    E07.FR.03: When a transaction is locally stopped by idToken, the Charging Station sends a TransactionEventRequest(eventType=Ended, triggerReason=StopAuthorized).
System under test   CSMS

Description         This test case covers how the CSMS can remotely request the Charging Station to reset itself
                    by sending a ResetRequest during a transaction. When ResetRequest "OnIdle" is sent the charging
                    stations schedules a reboot after all transactions are stopped.
Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP specification.

Prerequisite(s)     n/a

Before (Reusable State): EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to reboot the Charging Station with status OnIdle
1. The CSMS sends a ResetRequest (type: OnIdle)
2. The OCTT responds with a ResetResponse with status Scheduled
3. The OCTT sends a TransactionEventRequest (Updated, StopAuthorized)
4. The CSMS responds with a TransactionEventResponse
5. The OCTT sends a TransactionEventRequest (Ended, EVCommunicationLost)
6. The CSMS responds with a TransactionEventResponse
7. The OCTT sends a BootNotificationRequest with reason ScheduledReset
8. The CSMS responds with a BootNotificationResponse (status: Accepted)
9. The OCTT notifies the CSMS about the current state of all connectors.
10. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: ResetRequest
    - type OnIdle
    - evseId must be omitted
* Step 8:
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
async def test_tc_b_21():
    """Reset CS - With Ongoing Transaction - OnIdle: scheduled reset after transaction ends."""
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
    cp._reset_response_status = ResetStatusEnumType.scheduled
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Simulate EnergyTransferStarted state - start a transaction
    transaction_id = generate_transaction_id()

    # Send TransactionEvent Started
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

    # Trigger CSMS to send ResetRequest with type OnIdle
    trigger_task = asyncio.create_task(reset(BASIC_AUTH_CP, "OnIdle"))

    await asyncio.wait_for(
        cp._received_reset.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task

    assert cp._reset_data is not None
    assert cp._reset_data['type'] == 'OnIdle', \
        f"Expected OnIdle reset type, got: {cp._reset_data['type']}"
    # Tool validation: evseId must be omitted for Charging Station reset
    assert cp._reset_data['evse_id'] is None, \
        f"Expected evseId to be omitted, got: {cp._reset_data['evse_id']}"

    # Step 3-4: Send TransactionEventRequest (Updated, StopAuthorized)
    updated_event = TransactionEvent(
        event_type='Updated',
        timestamp=now_iso(),
        trigger_reason='StopAuthorized',
        seq_no=1,
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': 'EVConnected',
        },
        id_token={'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
    )
    await cp.send_transaction_event_request(updated_event)

    # Step 5-6: Send TransactionEventRequest (Ended, EVCommunicationLost)
    ended_event = TransactionEvent(
        event_type='Ended',
        timestamp=now_iso(),
        trigger_reason='EVCommunicationLost',
        seq_no=2,
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': 'Idle',
            'stopped_reason': 'EVDisconnected',
        },
    )
    await cp.send_transaction_event_request(ended_event)

    # Close connection to simulate reset
    start_task.cancel()
    await ws.close()

    # Step 7-8: Reconnect with ScheduledReset reason
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification_with_reason('ScheduledReset')
    assert boot_response is not None
    assert boot_response.status == RegistrationStatusEnumType.accepted

    # Step 9-10: Notify CSMS about connector states
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
