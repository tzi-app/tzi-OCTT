"""
Test case name      Show EV Driver Final Total Cost After Charging
Test case Id        TC_I_02_CSMS
Use case Id(s)      I03
Requirement(s)      I03.FR.02

Requirement Details:
    I03.FR.02: The CSMS SHALL send the total cost of the transaction in the totalCost field of the
               TransactionEventResponse message.
        Precondition: I03.FR.01 AND When Total Cost is known to the CSMS.
System under test   CSMS

Description         While a transaction is ongoing, the driver wants to know how much the running total cost
                    is, updated at a relevant interval.

Purpose             To verify if the CSMS is able to correctly send the total cost as described in the OCPP
                    specification.

Prerequisite(s)     - N/a

Configuration State N/a

Memory State        - CSMS is configured with a tariff which is based on energy consumed.

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State EVConnectedPreSession
    - The TransactionEventRequest contains the MeterValue field.
    - sampledValue[0].value 1000
    - sampledValue[0].context Transaction.Begin
2. Execute Reusable State Authorized
3. Execute Reusable State EnergyTransferStarted
4. Execute Reusable State StopAuthorized
5. Execute Reusable State EVConnectedPostSession
6. The Test System notifies the CSMS about the current state of the configured connector.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
7. The CSMS responds accordingly.
8. The Test System sends a TransactionEventRequest with
    - triggerReason EVCommunicationLost
    - eventType Ended
    - transactionInfo.chargingState Idle
    - transactionInfo.stoppedReason EVDisconnected
    - meterValue[0].sampledValue[0].value 6000
    - meterValue[0].sampledValue[0].context Transaction.End
9. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 9:
    Message TransactionEventResponse
    - totalCost <Not omitted>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.authorized import authorized
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_connected_post_session import ev_connected_post_session
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from reusable_states.stop_authorized import stop_authorized
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_i_02(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Memory State: CSMS is configured with a tariff which is based on energy consumed.

    # 1. Execute Reusable State EVConnectedPreSession
    #    - The TransactionEventRequest contains the MeterValue field.
    #    - sampledValue[0].value 1000
    #    - sampledValue[0].context Transaction.Begin
    transaction_id = await ev_connected_pre_session(cp, meter_value=[{
        'timestamp': utc_now_iso(),
        'sampled_value': [{'value': 1000, 'context': 'Transaction.Begin'}],
    }])

    # 2. Execute Reusable State Authorized
    await authorized(cp)

    # 3. Execute Reusable State EnergyTransferStarted
    await energy_transfer_started(cp)

    # 4. Execute Reusable State StopAuthorized
    await stop_authorized(cp)

    # 5. Execute Reusable State EVConnectedPostSession
    await ev_connected_post_session(cp)

    # 6. The Test System notifies the CSMS about the current state of the configured connector.
    #    Message: StatusNotificationRequest
    #    - connectorStatus Available
    #    Message: NotifyEventRequest
    #    - trigger Delta
    #    - actualValue "Available"
    #    - component.name "Connector"
    #    - variable.name "AvailabilityState"
    # 7. The CSMS responds accordingly.
    await cp.send_connector_status('Available', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    # 8. The Test System sends a TransactionEventRequest with
    #    - triggerReason EVCommunicationLost
    #    - eventType Ended
    #    - transactionInfo.chargingState Idle
    #    - transactionInfo.stoppedReason EVDisconnected
    #    - meterValue[0].sampledValue[0].value 6000
    #    - meterValue[0].sampledValue[0].context Transaction.End
    # 9. The CSMS responds with a TransactionEventResponse
    response = await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='EVCommunicationLost',
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': 'Idle',
            'stopped_reason': 'EVDisconnected',
        },
        meter_value=[{
            'timestamp': utc_now_iso(),
            'sampled_value': [{'value': 6000, 'context': 'Transaction.End'}],
        }],
    ))
    assert response.total_cost is not None, "TransactionEventResponse.totalCost must not be omitted"

    start_task.cancel()
