"""
State               EVConnectedPreSession
System under test   CSMS
Description         This state will simulate that the EV and EVSE of the simulated Charging Station are
                    connected.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

1. The Test System notifies the CSMS about the status change of the connector
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

If State is Authorized then
    eventType is Updated
else
    eventType is Started

4. The CSMS responds with a TransactionEventResponse

Tool validations
N/a
Post condition      State is EVConnectedPreSession
"""

import os

from ocpp.v21 import call

from charge_point import ChargingSession, TziChargePoint21
from ocpp_messages import utc_now_iso

CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


async def ev_connected_pre_session(cp: TziChargePoint21, evse_id: int = CONFIGURED_EVSE_ID,
                                   connector_id: int = CONFIGURED_CONNECTOR_ID,
                                   session: ChargingSession = None,
                                   starts_transaction: bool = True, meter_value: list = None):
    """Returns the id of the transaction.

    meter_value: the MeterValue field of the TransactionEventRequest, for the test cases
        that have one in this state.

    session: the charging session this is about, when the scenario has more than one.
    starts_transaction: False for a Charging Station of which the TxStartPoint is not reached
        when the EV is connected. The scenario of such a test case sends the
        TransactionEventRequest with eventType Started itself, so steps 3 and 4 of this
        state are left out: the EV is connected, and there is no transaction yet.
    """
    session = session or cp.session
    # 1. The Test System notifies the CSMS about the status change of the connector
    #    Message: StatusNotificationRequest - connectorStatus is Occupied
    #    Message: NotifyEventRequest - trigger is Delta, actualValue is Occupied,
    #             component.name is Connector, variable.name is AvailabilityState
    # 2. The CSMS responds accordingly.
    await cp.send_connector_status('Occupied', evse_id=evse_id, connector_id=connector_id)
    session.ev_connected = True
    session.evse_id = evse_id
    session.connector_id = connector_id
    if not starts_transaction and session.transaction_id is None:
        session.state = 'EVConnectedPreSession'
        return None

    # 3. The Test System sends a TransactionEventRequest With triggerReason is CablePluggedIn
    #    transactionInfo.chargingState is EVConnected, evse.id <Configured evseId>,
    #    evse.connectorId <Configured connectorId>. If State is Authorized then eventType is
    #    Updated, else eventType is Started.
    # 4. The CSMS responds with a TransactionEventResponse
    if session.transaction_id is None:
        event_type = 'Started'
        session.start_transaction()
    else:
        event_type = 'Updated'
    await cp.call(call.TransactionEvent(
        event_type=event_type,
        timestamp=utc_now_iso(),
        trigger_reason='CablePluggedIn',
        seq_no=session.next_seq_no(),
        transaction_info={'transaction_id': session.transaction_id, 'charging_state': 'EVConnected'},
        evse={'id': evse_id, 'connector_id': connector_id},
        meter_value=meter_value,
    ))

    session.state = 'EVConnectedPreSession'
    return session.transaction_id
