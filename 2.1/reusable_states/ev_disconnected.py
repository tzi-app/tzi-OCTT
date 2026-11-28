"""
State               EVDisconnected
System under test   CSMS
Description         This state will simulate that the EV and EVSE of the simulated Charging Station are
                    disconnected, after the charging session is authorized to stop.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      If State is NOT EVConnectedPostSession then execute Reusable State
                            EVConnectedPostSession

Main

1. The Test System notifies the CSMS about the status change of the connector.
   Message: StatusNotificationRequest
   - connectorStatus is Available
   Message: NotifyEventRequest
   - trigger is Delta
   - actualValue is Available
   - component.name is Connector
   - variable.name is AvailabilityState
2. The CSMS responds accordingly.
3. The Test System sends a TransactionEventRequest With triggerReason is EVCommunicationLost
   transactionInfo.chargingState is Idle
   transactionInfo.stoppedReason is EVDisconnected
   eventType is Ended
4. The CSMS responds with a TransactionEventResponse

Tool validations
N/a
Post condition      State is EVDisconnected
"""

from ocpp.v21 import call

from charge_point import ChargingSession, TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.ev_connected_post_session import ev_connected_post_session


async def ev_disconnected(cp: TziChargePoint21, session: ChargingSession = None,
                          from_current_state: bool = False, ends_transaction: bool = True,
                          meter_value=None):
    """session: the charging session this is about, when the scenario has more than one.

    meter_value: the MeterValue field of the TransactionEventRequest, for the test cases
        that have one in this state: a list, or a function that gives the list when the
        request is sent.

    from_current_state: the scenario itself says from which state the EV is disconnected (a
        test case that has "Execute Reusable State EVDisconnected" as a step, in another
        state than EVConnectedPostSession). Only the main steps are executed then.
    ends_transaction: False for a Charging Station of which the TxStopPoint is not reached
        when the EV is disconnected (ParkingBayOccupancy): the transaction goes on, so the
        TransactionEventRequest has eventType Updated and no stoppedReason.
    """
    session = session or cp.session

    # Before: If State is NOT EVConnectedPostSession then execute Reusable State
    #         EVConnectedPostSession
    if session.state != 'EVConnectedPostSession' and not from_current_state:
        await ev_connected_post_session(cp, session=session)

    # 1. The Test System notifies the CSMS about the status change of the connector.
    #    Message: StatusNotificationRequest - connectorStatus is Available
    #    Message: NotifyEventRequest - trigger is Delta, actualValue is Available,
    #             component.name is Connector, variable.name is AvailabilityState
    # 2. The CSMS responds accordingly.
    await cp.send_connector_status('Available', evse_id=session.evse_id, connector_id=session.connector_id)

    # 3. The Test System sends a TransactionEventRequest With triggerReason is
    #    EVCommunicationLost, transactionInfo.chargingState is Idle,
    #    transactionInfo.stoppedReason is EVDisconnected, eventType is Ended
    # 4. The CSMS responds with a TransactionEventResponse
    transaction_info = {'transaction_id': session.transaction_id, 'charging_state': 'Idle'}
    if ends_transaction:
        transaction_info['stopped_reason'] = 'EVDisconnected'
    await cp.call(call.TransactionEvent(
        event_type='Ended' if ends_transaction else 'Updated',
        timestamp=utc_now_iso(),
        trigger_reason='EVCommunicationLost',
        seq_no=session.next_seq_no(),
        transaction_info=transaction_info,
        meter_value=meter_value() if callable(meter_value) else meter_value,
    ))

    session.state = 'EVDisconnected'
    session.authorized = False
    session.ev_connected = False
    if ends_transaction:
        session.transaction_id = None
        session.id_token = None
