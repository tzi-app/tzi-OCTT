"""
TC_J_09 - Sampled Meter Values - EventType Updated
Use case: J02 | Requirement: J02.FR.19
J02.FR.19: When CSMS receives a TransactionEventRequest CSMS SHALL respond with TransactionEventResponse. Failing to respond with TransactionEventRespon se might cause the Charging Station to try the same message
    Precondition: When CSMS receives a TransactionEventRequest
System under test: CSMS

Description:
    The Charging Station samples the electrical meter or other sensor/transducer hardware to provide
    information about its Meter Values. Depending on configuration settings, the Charging Station will
    send Meter Values.

Purpose:
    To verify if the CSMS is able to handle a Charging Station sending sampled Meter Values, when
    there is an ongoing transaction.

Before:
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): State is EnergyTransferStarted

Main:
    1. The OCTT sends a TransactionEventRequest
       With triggerReason is MeterValuePeriodic, eventType is Updated
         - sampledValue.context is Sample.Periodic

    2. The CSMS responds with a TransactionEventResponse

    Note(s):
      - This step will be executed every sampled interval.
      - The OCTT will end the testcase after three MeterValues.

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    VALID_ID_TOKEN            - Valid idToken value
    VALID_ID_TOKEN_TYPE       - Valid idToken type
    CONFIGURED_EVSE_ID        - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.call import TransactionEvent
from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ChargingStateEnumType as ChargingStateType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
SAMPLED_METER_VALUES_INTERVAL = int(os.environ['SAMPLED_METER_VALUES_INTERVAL'])

METER_VALUE_COUNT = 3


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_j_09(connection):
    """Sampled Meter Values - EventType Updated (J02.FR.19).
    J02.FR.19: When CSMS receives a TransactionEventRequest CSMS SHALL respond with TransactionEventResponse. Failing to respond with TransactionEventRespon se might cause the Charging Station to try the same message
        Precondition: When CSMS receives a TransactionEventRequest
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Boot
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Before: EnergyTransferStarted
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Step 1-2: Send 3 TransactionEventRequest with MeterValuePeriodic
    for i in range(METER_VALUE_COUNT):
        meter_periodic_event = TransactionEvent(
            event_type=TransactionEventType.updated,
            timestamp=now_iso(),
            trigger_reason=TriggerReasonType.meter_value_periodic,
            seq_no=cp.next_seq_no(),
            transaction_info={
                'transaction_id': transaction_id,
                'charging_state': ChargingStateType.charging,
            },
            evse={
                'id': EVSE_ID,
                'connector_id': CONNECTOR_ID,
            },
            meter_value=[{
                'timestamp': now_iso(),
                'sampled_value': [{
                    'value': float((i + 1) * 100),
                    'context': 'Sample.Periodic',
                }],
            }],
        )
        tx_response = await cp.send_transaction_event_request(meter_periodic_event)
        assert tx_response is not None

        if i < METER_VALUE_COUNT - 1:
            await asyncio.sleep(SAMPLED_METER_VALUES_INTERVAL)

    start_task.cancel()
