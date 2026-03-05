"""
TC_G_11 - Change Availability EVSE - With ongoing transaction
Use case: G03 | Requirements: N/a
System under test: CSMS

Description:
    This test case covers how the CSMS requests the Charging Station to change the availability of one
    of the EVSEs from Operative to Inoperative. An EVSE is considered Operative in any status other than
    Faulted and Unavailable.

Purpose:
    To verify if the CSMS is able to send a change availability request during a transaction according
    to the mechanism as described at the OCPP specification.

Before:
    State is EnergyTransferStarted

Main:
    Note: Request the CSMS to change the availability to inoperative
    1. The CSMS sends a ChangeAvailabilityRequest
    2. CS responds with ChangeAvailabilityResponse (status=Scheduled)
    Note: Wait for <Configured Transaction Duration>
    3. Execute Reusable State StopAuthorized
    4. Execute Reusable State EVConnectedPostSession
    5. Execute Reusable State EVDisconnected
    6. CS notifies CSMS (StatusNotificationRequest connectorStatus=Unavailable)
    7. The CSMS responds accordingly.

Tool validations:
    * Step 1: ChangeAvailabilityRequest
      - operationalStatus = Inoperative
      - evse.id = <Configured evseId>
      - connectorId = omit

Post scenario validations:
    - A respond to report the state of a connector has been received for all connectors.

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
    OperationalStatusEnumType,
    ChangeAvailabilityStatusEnumType,
    EventTriggerEnumType,
    EventNotificationEnumType,
)
from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context
from trigger import send_call
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
async def test_tc_g_11():
    """Change Availability EVSE - With ongoing transaction."""
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
    cp._change_availability_response_status = ChangeAvailabilityStatusEnumType.scheduled
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available, evse_id=EVSE_ID)

    # Before: Execute Reusable State EnergyTransferStarted
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Step 1-2: Trigger CSMS to send ChangeAvailabilityRequest (EVSE-level Inoperative)
    async def trigger_change_availability():
        await asyncio.sleep(1)
        await send_call(BASIC_AUTH_CP, "ChangeAvailability", {
            "operationalStatus": "Inoperative",
            "evse": {"id": EVSE_ID},
        })

    trigger_task = asyncio.create_task(trigger_change_availability())

    await asyncio.wait_for(
        cp._received_change_availability.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    # Validate ChangeAvailabilityRequest content
    assert cp._change_availability_data is not None
    req_data = cp._change_availability_data
    assert req_data['operational_status'] == OperationalStatusEnumType.inoperative or \
           req_data['operational_status'] == 'Inoperative', \
        f"Expected operationalStatus=Inoperative, got {req_data['operational_status']}"

    # Validate evse.id per tool validations
    evse = req_data.get('evse')
    assert evse is not None, "Expected evse to be present for EVSE-level change"
    if isinstance(evse, dict):
        assert evse.get('id') == EVSE_ID, \
            f"Expected evse.id={EVSE_ID}, got {evse.get('id')}"
        assert evse.get('connector_id') is None and evse.get('connectorId') is None, \
            f"Expected evse.connectorId to be omitted, got {evse}"

    # CS responded with Scheduled (set before start)

    # Note: Wait for <Configured Transaction Duration>
    await asyncio.sleep(TRANSACTION_DURATION)

    # Step 3: Execute Reusable State StopAuthorized
    await stop_authorized(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                          transaction_id=transaction_id)

    # Step 4: Execute Reusable State EVConnectedPostSession
    await ev_connected_post_session(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                    transaction_id=transaction_id)

    # Step 5: Execute Reusable State EVDisconnected
    await ev_disconnected(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                          transaction_id=transaction_id)

    # Step 6: CS notifies CSMS about the current state - Unavailable
    await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusEnumType.unavailable,
        evse_id=EVSE_ID,
    )

    # NotifyEventRequest
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

    logging.info("TC_G_11 completed successfully")
    start_task.cancel()
    await ws.close()
