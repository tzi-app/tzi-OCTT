"""
TC_I_01 - Show EV Driver running total cost during charging - costUpdatedRequest
Use case: I02 | Requirements: I02.FR.01
I02.FR.01: The CSMS SHALL send either a CostUpdatedRequest at a relevant interval/moment or return the running cost in a TransactionEventResponse. This might depend on the charging speed, running cost, etc.
System under test: CSMS

Description:
    The CSMS sends CostUpdatedRequest messages to the Charging Station during an ongoing
    charging session to communicate the running total cost to the EV Driver.

Purpose:
    To verify if the CSMS sends CostUpdatedRequest messages with the running total cost
    after receiving TransactionEventRequests with periodic meter values, when the
    TransactionEventResponse does not include a totalCost.

Main:
    1. CS sends AuthorizeRequest with idToken
    2. CSMS responds AuthorizeResponse (status Accepted)
    3. CS sends TransactionEventRequest (triggerReason Authorized, eventType Updated)
    4. CSMS responds TransactionEventResponse (status Accepted)
    5. Execute Reusable State EVConnectedPreSession
    6. Execute Reusable State EnergyTransferStarted (Part 2 only - charging state changed)
    7. CS sends TransactionEventRequest (triggerReason MeterValuePeriodic, eventType Updated,
       sampledValue.context Sample.Periodic)
    8. CSMS responds TransactionEventResponse
    9. If no totalCost in TransactionEventResponse, CSMS sends CostUpdatedRequest (transactionId)
   10. CS responds CostUpdatedResponse
   11. Steps 7-10 repeated (2 MeterValue iterations total)

Tool validations:
    * Step 2: AuthorizeResponse - idTokenInfo.status must be Accepted
    * Step 4: TransactionEventResponse - idTokenInfo.status must be Accepted
    * Step 9: CostUpdatedRequest - transactionId must match the transaction

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
    VALID_ID_TOKEN            - Valid idToken value
    VALID_ID_TOKEN_TYPE       - Valid idToken type
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.call import TransactionEvent
from ocpp.v201.datatypes import EventDataType, ComponentType, VariableType
from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    AuthorizationStatusEnumType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
    EventTriggerEnumType as EventTriggerType,
    EventNotificationEnumType as EventNotificationType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
SAMPLED_METER_VALUES_INTERVAL = float(os.environ['SAMPLED_METER_VALUES_INTERVAL'])
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']


@pytest.mark.asyncio
async def test_tc_i_01():
    """Show EV Driver running total cost during charging - costUpdatedRequest."""
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

    # Step 1-2: Authorize
    authorize_response = await cp.send_authorization_request(
        id_token=VALID_ID_TOKEN, token_type=VALID_ID_TOKEN_TYPE
    )
    assert authorize_response is not None
    assert authorize_response.id_token_info.status == AuthorizationStatusEnumType.accepted

    # Step 3-4: TransactionEvent Updated (triggerReason Authorized)
    started_event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.authorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
        },
        id_token={
            'id_token': VALID_ID_TOKEN,
            'type': VALID_ID_TOKEN_TYPE,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    started_response = await cp.send_transaction_event_request(started_event)
    assert started_response is not None
    if started_response.id_token_info is not None:
        assert started_response.id_token_info.status == AuthorizationStatusEnumType.accepted

    # Step 5: Reusable State EVConnectedPreSession
    # StatusNotification - Occupied
    await cp.send_status_notification(
        connector_id=CONNECTOR_ID,
        status=ConnectorStatusEnumType.occupied,
    )

    # NotifyEvent - Occupied
    event_data = [
        EventDataType(
            trigger=EventTriggerType.delta,
            actual_value='Occupied',
            component=ComponentType(name='Connector'),
            variable=VariableType(name='AvailabilityState'),
            timestamp=now_iso(),
            event_id=EVSE_ID,
            event_notification_type=EventNotificationType.custom_monitor,
        )
    ]
    await cp.send_notify_event(data=event_data)

    # TransactionEvent Updated - CablePluggedIn / EVConnected
    cable_plugged_event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.cable_plugged_in,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.ev_connected,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    cable_response = await cp.send_transaction_event_request(cable_plugged_event)
    assert cable_response is not None

    # Step 6: Reusable State EnergyTransferStarted (Part 2 - already connected)
    # TransactionEvent Updated - ChargingStateChanged / Charging
    charging_event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.charging_state_changed,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': ChargingStateType.charging,
        },
        evse={
            'id': EVSE_ID,
            'connector_id': CONNECTOR_ID,
        },
    )
    charging_response = await cp.send_transaction_event_request(charging_event)
    assert charging_response is not None

    # Steps 7-10: Send MeterValue periodic updates (2 iterations)
    # After each TransactionEventResponse, if no totalCost, expect CostUpdatedRequest from CSMS
    #
    # Energy is calculated as MAX(meter) - MIN(meter). The first meter reading
    # alone yields delta=0 (only one data point), so cost won't change from the
    # session fee. The initial CostUpdated (sent at transaction start) satisfies
    # iteration 0. Iteration 1 adds a second reading, producing a real energy
    # delta and a genuine cost change that triggers a fresh CostUpdated.
    for i in range(2):
        if i > 0:
            await asyncio.sleep(SAMPLED_METER_VALUES_INTERVAL)
            cp._received_cost_updated.clear()

        meter_event = TransactionEvent(
            event_type=TransactionEventType.updated,
            timestamp=now_iso(),
            trigger_reason=TriggerReasonType.meter_value_periodic,
            seq_no=cp.next_seq_no(),
            transaction_info={
                'transaction_id': transaction_id,
                'charging_state': ChargingStateType.charging,
            },
            meter_value=[{
                'timestamp': now_iso(),
                'sampled_value': [{
                    'value': float((i + 1) * 1000),
                    'context': 'Sample.Periodic',
                }],
            }],
        )
        meter_response = await cp.send_transaction_event_request(meter_event)
        assert meter_response is not None

        # If the TransactionEventResponse does not include totalCost,
        # the CSMS should send a CostUpdatedRequest
        if meter_response.total_cost is None:
            # Wait for a CostUpdated matching THIS transaction (the CSMS periodic
            # sweep may deliver CostUpdated for stale transactions from prior runs).
            deadline = asyncio.get_event_loop().time() + CSMS_ACTION_TIMEOUT
            matched = False
            while asyncio.get_event_loop().time() < deadline:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    break
                try:
                    await asyncio.wait_for(
                        cp._received_cost_updated.wait(),
                        timeout=remaining,
                    )
                except asyncio.TimeoutError:
                    break
                if cp._cost_updated_data and cp._cost_updated_data['transaction_id'] == transaction_id:
                    matched = True
                    break
                # Wrong transaction — clear and keep waiting
                logging.info(
                    f"Ignoring CostUpdated for stale transaction "
                    f"{cp._cost_updated_data.get('transaction_id')}"
                )
                cp._received_cost_updated.clear()

            if not matched:
                pytest.fail(
                    f"CSMS did not send CostUpdatedRequest within {CSMS_ACTION_TIMEOUT}s "
                    f"after MeterValue iteration {i + 1} (and TransactionEventResponse had no totalCost)"
                )
            logging.info(
                f"Received CostUpdatedRequest (iteration {i + 1}): "
                f"totalCost={cp._cost_updated_data['total_cost']}, "
                f"transactionId={cp._cost_updated_data['transaction_id']}"
            )
        else:
            logging.info(
                f"TransactionEventResponse included totalCost={meter_response.total_cost} "
                f"(iteration {i + 1}), CostUpdatedRequest not required"
            )

    logging.info("TC_I_01 completed successfully")
    start_task.cancel()
    await ws.close()
