"""
Test case name      Disconnect cable on EV-side - Suspend transaction
Test case Id        TC_E_26_CSMS
Use case Id(s)      E10
Requirement(s)      E10.FR.01

Requirement Details:
    E10.FR.01: The Connector SHALL remain locked at the Charging Station until the EV Driver presents the
               IdToken.
        Precondition: If StopTxOnEVSideDisconnect = false AND Cable not permanently attached
System under test   CSMS

Description         The Charging Station can behave in several different ways when the cable is disconnected
                    at the EV side, based on its configuration. This test case tests one of the possible
                    configuration settings.

Purpose             To verify if the CSMS can handle a Charging Station that suspends the transaction when the
                    EV and EVSE are disconnected at the EV side AND is able restart the energy transfer after
                    reconnecting the EV and EVSE.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferSuspended

Test Scenario
1. The Test System sends a TransactionEventRequest
    With triggerReason is EVCommunicationLost
    transactionInfo.chargingState is Idle
    eventType is Updated
2. The CSMS responds with a TransactionEventResponse
3. The Test System notifies the CSMS about the current state of the connector.
    Message: StatusNotificationRequest
    - connectorStatus Available
    - evseId <Configured evseId>
    - connectorId <Configured connectorId>
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - component.evse.id <Configured evseId>
    - component.evse.connectorid <Configured connectorId>
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.
5. The Test System sends a TransactionEventRequest
    With triggerReason is CablePluggedIn
    transactionInfo.chargingState is EVConnected
    eventType is Updated
6. The CSMS responds with a TransactionEventResponse
7. The Test System sends a TransactionEventRequest
    With triggerReason is ChargingStateChanged
    transactionInfo.chargingState is Charging
    eventType is Updated
8. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_suspended import energy_transfer_suspended
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_26(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferSuspended
    await energy_transfer_suspended(cp)
    transaction_id = cp.session.transaction_id

    # 1. The Test System sends a TransactionEventRequest
    #    With triggerReason is EVCommunicationLost
    #    transactionInfo.chargingState is Idle
    #    eventType is Updated
    # 2. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='EVCommunicationLost',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'Idle'},
    ))

    # 3. The Test System notifies the CSMS about the current state of the connector.
    #    Message: StatusNotificationRequest
    #    - connectorStatus Available
    #    - evseId <Configured evseId>
    #    - connectorId <Configured connectorId>
    #    Message: NotifyEventRequest
    #    - trigger Delta
    #    - actualValue "Available"
    #    - component.name "Connector"
    #    - component.evse.id <Configured evseId>
    #    - component.evse.connectorid <Configured connectorId>
    #    - variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    await cp.send_connector_status('Available', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    # 5. The Test System sends a TransactionEventRequest
    #    With triggerReason is CablePluggedIn
    #    transactionInfo.chargingState is EVConnected
    #    eventType is Updated
    # 6. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='CablePluggedIn',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'EVConnected'},
    ))

    # 7. The Test System sends a TransactionEventRequest
    #    With triggerReason is ChargingStateChanged
    #    transactionInfo.chargingState is Charging
    #    eventType is Updated
    # 8. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='ChargingStateChanged',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'Charging'},
    ))

    start_task.cancel()
