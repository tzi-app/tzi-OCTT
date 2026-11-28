"""
Test case name      Sampled Meter Values - EventType Ended
Test case Id        TC_J_10_CSMS
Use case Id(s)      J02
Requirement(s)      J02.FR.19

Requirement Details:
    J02.FR.19: CSMS SHALL respond with TransactionEventResponse.
        Precondition: When CSMS receives a TransactionEventRequest
        Note: Failing to respond with TransactionEventResponse might cause the Charging Station to try the
              same message again.
System under test   CSMS

Description         The Charging Station samples the electrical meter or other sensor/transducer hardware to
                    provide information about its Meter Values. Depending on configuration settings, the
                    Charging Station will send Meter Values.

Purpose             To verify if the CSMS is able to handle a Charging Station sending sampled Meter Values,
                    when a transaction ends.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. Execute Reusable State EVDisconnected
    - The TransactionEventRequest containing eventType Ended contains the MeterValue field.
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured value at configured clock-aligned Tx ended Meter Values interval>.
    - sampledValue.context is Sample.Periodic AND the last one has Transaction.End

    Note(s):
    - This step will be executed after the _<Configured transaction duration> is reached._
    - This causes the transaction to stop.

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from metering import EnergyMeter, MeterValueSampler
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_disconnected import ev_disconnected
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
TX_ENDED_METER_VALUES_INTERVAL = int(os.environ['TX_ENDED_METER_VALUES_INTERVAL'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_j_10(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    await energy_transfer_started(cp)
    # From here the station keeps the periodic readings of the meter for the end of the
    # transaction: one every <configured Tx ended Meter Values interval>.
    sampler = MeterValueSampler(EnergyMeter(power=11000), TX_ENDED_METER_VALUES_INTERVAL,
                                context='Sample.Periodic')

    # 1. Execute Reusable State EVDisconnected
    #    - The TransactionEventRequest containing eventType Ended contains the MeterValue field.
    #    - timestamp <The intervals between the timestamps of the received Meter Value messages
    #      equals the configured value at configured clock-aligned Tx ended Meter Values
    #      interval>.
    #    - sampledValue.context is Sample.Periodic AND the last one has Transaction.End
    #    Note(s):
    #    - This step will be executed after the <Configured transaction duration> is reached
    #      (the wait of the state StopAuthorized).
    #    - This causes the transaction to stop.
    await ev_disconnected(cp, meter_value=sampler.stop)

    start_task.cancel()
