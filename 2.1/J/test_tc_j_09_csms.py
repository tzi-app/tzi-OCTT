"""
Test case name      Sampled Meter Values - EventType Updated
Test case Id        TC_J_09_CSMS
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
                    when there is an ongoing transaction.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System sends a TransactionEventRequest With
    - triggerReason is MeterValuePeriodic
    - eventType is Updated
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured sampled Meter Values interval>.
    - sampledValue.context is Sample.Periodic
    Note(s):
    _- This step will be executed every _<Configured sampled Meter Values interval>
    - The Test System will end the testcase after three MeterValues.
2. The CSMS responds with a TransactionEventResponse

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
from metering import EnergyMeter, ticks, utc_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
SAMPLED_METER_VALUES_INTERVAL = int(os.environ['SAMPLED_METER_VALUES_INTERVAL'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_j_09(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)
    meter = EnergyMeter(power=11000)

    # 1. The Test System sends a TransactionEventRequest With
    #    - triggerReason is MeterValuePeriodic
    #    - eventType is Updated
    #    - timestamp <The intervals between the timestamps of the received Meter Value messages
    #      equals the configured sampled Meter Values interval>.
    #    - sampledValue.context is Sample.Periodic
    #    Note(s):
    #    - This step will be executed every <Configured sampled Meter Values interval>
    #    - The Test System will end the testcase after three MeterValues.
    # 2. The CSMS responds with a TransactionEventResponse
    times_sent = 0
    async for moment in ticks(SAMPLED_METER_VALUES_INTERVAL):
        await cp.call(call.TransactionEvent(
            event_type='Updated',
            timestamp=utc_iso(moment),
            trigger_reason='MeterValuePeriodic',
            seq_no=cp.next_seq_no(),
            transaction_info={'transaction_id': transaction_id},
            meter_value=[meter.meter_value('Sample.Periodic', at=moment)],
        ))
        times_sent += 1
        if times_sent == 3:
            break

    start_task.cancel()
