"""
State               EnergyTransferStarted
System under test   CSMS
Description         This state will simulate that there is transferring energy between the EV and EVSE of the
                    simulated Charging Station.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      If State is NOT Authorized then execute Reusable State Authorized
                            If EVConnected is true, then proceed to part 2
                            Else proceed to part 1.

Main

Main (Part 1)

1. The Test System notifies the CSMS about the status change of the connector.
   Message: StatusNotificationRequest
   - connectorStatus is Occupied
   Message: NotifyEventRequest
   - trigger is Delta
   - actualValue is Occupied
   - component.name is Connector
   - variable.name is AvailabilityState
2. The CSMS responds accordingly.
3. The Test System sends a TransactionEventRequest With triggerReason is CablePluggedIn
   transactionInfo.chargingState is EVConnected
   evse.id <Configured evseId>
   evse.connectorId <Configured connectorId>
   eventType is Updated
4. The CSMS responds with a TransactionEventResponse

Main (Part 2)

5. The Test System sends a TransactionEventRequest With triggerReason is ChargingStateChanged
   transactionInfo.chargingState is Charging
   eventType is Updated
6. The CSMS responds with a TransactionEventResponse

Tool validations
N/a
Post condition      State is EnergyTransferStarted
                    EVConnected is true
"""

import os

from ocpp.v21 import call

from charge_point import ChargingSession, TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.authorized import VALID_ID_TOKEN, VALID_ID_TOKEN_TYPE, authorized

CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


async def energy_transfer_started(cp: TziChargePoint21, evse_id: int = CONFIGURED_EVSE_ID,
                                  connector_id: int = CONFIGURED_CONNECTOR_ID,
                                  id_token: str = VALID_ID_TOKEN,
                                  id_token_type: str = VALID_ID_TOKEN_TYPE,
                                  session: ChargingSession = None):
    """Returns the id of the transaction.

    session: the charging session this is about, when the scenario has more than one."""
    session = session or cp.session

    # Before: If State is NOT Authorized then execute Reusable State Authorized
    if not session.authorized:
        await authorized(cp, id_token=id_token, id_token_type=id_token_type, session=session)

    # If EVConnected is true, then proceed to part 2. Else proceed to part 1.
    if not session.ev_connected:
        # Main (Part 1)
        # 1. The Test System notifies the CSMS about the status change of the connector.
        #    Message: StatusNotificationRequest - connectorStatus is Occupied
        #    Message: NotifyEventRequest - trigger is Delta, actualValue is Occupied,
        #             component.name is Connector, variable.name is AvailabilityState
        # 2. The CSMS responds accordingly.
        await cp.send_connector_status('Occupied', evse_id=evse_id, connector_id=connector_id)

        # 3. The Test System sends a TransactionEventRequest With triggerReason is
        #    CablePluggedIn, transactionInfo.chargingState is EVConnected, evse.id <Configured
        #    evseId>, evse.connectorId <Configured connectorId>, eventType is Updated
        # 4. The CSMS responds with a TransactionEventResponse
        await cp.call(call.TransactionEvent(
            event_type='Updated',
            timestamp=utc_now_iso(),
            trigger_reason='CablePluggedIn',
            seq_no=session.next_seq_no(),
            transaction_info={'transaction_id': session.transaction_id, 'charging_state': 'EVConnected'},
            evse={'id': evse_id, 'connector_id': connector_id},
        ))
        session.ev_connected = True
        session.evse_id = evse_id
        session.connector_id = connector_id

    # Main (Part 2)
    # 5. The Test System sends a TransactionEventRequest With triggerReason is
    #    ChargingStateChanged, transactionInfo.chargingState is Charging, eventType is Updated
    # 6. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='ChargingStateChanged',
        seq_no=session.next_seq_no(),
        transaction_info={'transaction_id': session.transaction_id, 'charging_state': 'Charging'},
    ))

    session.state = 'EnergyTransferStarted'
    return session.transaction_id
