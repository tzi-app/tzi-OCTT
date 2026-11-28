"""
State               StopAuthorized
System under test   CSMS
Description         This state will simulate that the Charging Station is in a state where the charging
                    session is authorized to stop.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      If State is NOT EnergyTransferStarted then execute Reusable State
                            EnergyTransferStarted

Main

Notes(s): The tool will wait for <Configured Transaction Duration> seconds

1. The Test System sends a TransactionEventRequest With triggerReason is StopAuthorized
   eventType is Updated
2. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2: Message: TransactionEventResponse - idTokenInfo.status must be Accepted
Post condition      State is StopAuthorized
"""

import asyncio
import os

from ocpp.v21 import call

from charge_point import ChargingSession, TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.energy_transfer_started import energy_transfer_started

TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


async def stop_authorized(cp: TziChargePoint21, id_token: str = None, id_token_type: str = None,
                          session: ChargingSession = None):
    """id_token: the idToken that authorizes the stop. By default it is the idToken that
    authorized the transaction.
    session: the charging session this is about, when the scenario has more than one."""
    session = session or cp.session

    # Before: If State is NOT EnergyTransferStarted then execute Reusable State
    #         EnergyTransferStarted
    if session.state != 'EnergyTransferStarted':
        await energy_transfer_started(cp, session=session)

    # Note: The tool will wait for <Configured Transaction Duration> seconds
    await asyncio.sleep(TRANSACTION_DURATION)

    # 1. The Test System sends a TransactionEventRequest With triggerReason is StopAuthorized,
    #    eventType is Updated. It has the idToken that authorizes the stop.
    # 2. The CSMS responds with a TransactionEventResponse
    token = session.id_token if id_token is None else {'id_token': id_token, 'type': id_token_type}
    response = await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='StopAuthorized',
        seq_no=session.next_seq_no(),
        transaction_info={'transaction_id': session.transaction_id},
        id_token=token,
    ))
    assert response.id_token_info is not None, \
        "TransactionEventResponse has no idTokenInfo, which is required when the request has an idToken"
    assert response.id_token_info.status == 'Accepted', \
        f"Expected TransactionEventResponse.idTokenInfo.status Accepted, got {response.id_token_info.status}"

    session.state = 'StopAuthorized'
    session.authorized = False
    return response
