"""
State               EnergyTransferSuspended
System under test   CSMS
Description         This state will simulate that the Charging Station is in a state where the energy transfer
                    is suspended by the EV.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      If State is NOT EnergyTransferStarted then execute Reusable State
                            EnergyTransferStarted

Main

Notes(s): The tool will wait for <Configured Transaction Duration> seconds

1. The Test System sends a TransactionEventRequest With triggerReason is ChargingStateChanged
   transactionInfo.chargingState is SuspendedEV
2. The CSMS responds with a TransactionEventResponse

Tool validations
N/a
Post condition      State is EnergyTransferSuspended
"""

import asyncio
import os

from ocpp.v21 import call

from charge_point import ChargingSession, TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.energy_transfer_started import energy_transfer_started

TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


async def energy_transfer_suspended(cp: TziChargePoint21, session: ChargingSession = None):
    """session: the charging session this is about, when the scenario has more than one."""
    session = session or cp.session

    # Before: If State is NOT EnergyTransferStarted then execute Reusable State
    #         EnergyTransferStarted
    if session.state != 'EnergyTransferStarted':
        await energy_transfer_started(cp, session=session)

    # Note: The tool will wait for <Configured Transaction Duration> seconds
    await asyncio.sleep(TRANSACTION_DURATION)

    # 1. The Test System sends a TransactionEventRequest With triggerReason is
    #    ChargingStateChanged, transactionInfo.chargingState is SuspendedEV
    # 2. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='ChargingStateChanged',
        seq_no=session.next_seq_no(),
        transaction_info={'transaction_id': session.transaction_id, 'charging_state': 'SuspendedEV'},
    ))

    session.state = 'EnergyTransferSuspended'
