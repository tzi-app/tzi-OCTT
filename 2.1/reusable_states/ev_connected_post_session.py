"""
State               EVConnectedPostSession
System under test   CSMS
Description         This state will simulate that the Charging Station is in a state where the energy transfer
                    has been stopped and the transaction is NOT authorized to resume energy transfer without
                    re-authorization.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      If State is NOT StopAuthorized then execute Reusable State StopAuthorized

Main

1. The Test System sends a TransactionEventRequest With triggerReason is ChargingStateChanged
   transactionInfo.chargingState is EVConnected
   eventType is Updated
2. The CSMS responds with a TransactionEventResponse

Tool validations
N/a
Post condition      State is EVConnectedPostSession
"""

from ocpp.v21 import call

from charge_point import ChargingSession, TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.stop_authorized import stop_authorized


async def ev_connected_post_session(cp: TziChargePoint21, session: ChargingSession = None):
    """session: the charging session this is about, when the scenario has more than one."""
    session = session or cp.session

    # Before: If State is NOT StopAuthorized then execute Reusable State StopAuthorized
    if session.state != 'StopAuthorized':
        await stop_authorized(cp, session=session)

    # 1. The Test System sends a TransactionEventRequest With triggerReason is
    #    ChargingStateChanged, transactionInfo.chargingState is EVConnected, eventType is
    #    Updated
    # 2. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='ChargingStateChanged',
        seq_no=session.next_seq_no(),
        transaction_info={'transaction_id': session.transaction_id, 'charging_state': 'EVConnected'},
    ))

    session.state = 'EVConnectedPostSession'
