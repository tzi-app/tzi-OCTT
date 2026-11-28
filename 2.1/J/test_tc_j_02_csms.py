"""
Test case name      Clock-aligned Meter Values - Transaction ongoing
Test case Id        TC_J_02_CSMS
Use case Id(s)      J01
Requirement(s)      J01.FR.18

Requirement Details:
    J01.FR.18: CSMS SHALL respond with MeterValuesResponse.
        Precondition: When CSMS receives a MeterValuesRequest
        Note: Failing to respond with MeterValuesResponse might cause the Charging Station to try the same
              message again.
System under test   CSMS

Description         The Charging Station samples the electrical meter or other sensor/transducer hardware to
                    provide information about its Meter Values. Depending on configuration settings, the
                    Charging Station will send Meter Values.

Purpose             To verify if the CSMS is able to handle a Charging Station sending clock-aligned Meter
                    Values, when there is an ongoing transaction.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted for <Configured evseId>

Test Scenario
1. The Test System notifies the CSMS about its measured Meter Values.
    Message: MeterValuesRequest
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured clock-aligned Meter Values interval>.
    - sampledValue.context is Sample.Clock
    Message: NotifyEventRequest
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured clock-aligned Meter Values interval>.
    - trigger is Periodic
    - component.name is FiscalMetering
    Note(s):
    - This step will be executed every _<Configured clock-aligned Meter Values interval>
    - This step will be executed for evseId=0 and all configured idle EVSE.
2. The CSMS responds accordingly.
3. The Test System sends a TransactionEventRequest With
    - triggerReason is MeterValueClock
    - eventType is Updated
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured clock-aligned Meter Values interval>.
    - sampledValue.context is Sample.Clock
    Note(s):
    - This step will be executed every _<Configured clock-aligned Meter Values interval>
    - The Test System will end the testcase after the _<Configured transaction duration> is reached._
4. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os
import time

import pytest
from ocpp.v21 import call

from charge_point import CONFIGURED_NUMBER_OF_EVSES, TziChargePoint21
from metering import EnergyMeter, ticks, utc_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CLOCK_ALIGNED_METER_VALUES_INTERVAL = int(os.environ['CLOCK_ALIGNED_METER_VALUES_INTERVAL'])
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])

# The power of the energy transfer of the transaction, in W
CHARGING_POWER = 11000


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_j_02(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted for <Configured evseId>
    transaction_id = await energy_transfer_started(cp, evse_id=CONFIGURED_EVSE_ID)
    transaction_meter = EnergyMeter(power=CHARGING_POWER)
    # The meters outside the transaction: the one of the Charging Station (evseId 0), which
    # sees the energy of the transaction as well, and those of the idle EVSEs.
    other_meters = {0: EnergyMeter(power=CHARGING_POWER)}
    for evse_id in range(1, CONFIGURED_NUMBER_OF_EVSES + 1):
        if evse_id != CONFIGURED_EVSE_ID:
            other_meters[evse_id] = EnergyMeter()

    end_of_test = time.time() + TRANSACTION_DURATION
    async for moment in ticks(CLOCK_ALIGNED_METER_VALUES_INTERVAL, clock_aligned=True):
        # 1. The Test System notifies the CSMS about its measured Meter Values.
        #    Message: MeterValuesRequest
        #    - timestamp <The intervals between the timestamps of the received Meter Value
        #      messages equals the configured clock-aligned Meter Values interval>.
        #    - sampledValue.context is Sample.Clock
        #    Message: NotifyEventRequest
        #    - timestamp <as above>
        #    - trigger is Periodic
        #    - component.name is FiscalMetering
        #    Note(s):
        #    - This step will be executed every <Configured clock-aligned Meter Values interval>
        #    - This step will be executed for evseId=0 and all configured idle EVSE.
        # 2. The CSMS responds accordingly.
        for evse_id, meter in other_meters.items():
            reading = meter.reading(moment)
            await cp.send_meter_values(
                evse_id, [{'value': reading, 'context': 'Sample.Clock'}], timestamp=utc_iso(moment))
            component = {'name': 'FiscalMetering'}
            if evse_id:
                component['evse'] = {'id': evse_id}
            await cp.send_event(component, 'EnergyImportRegister', str(reading), trigger='Periodic',
                                event_notification_type='PreconfiguredMonitor',
                                timestamp=utc_iso(moment))

        # 3. The Test System sends a TransactionEventRequest With
        #    - triggerReason is MeterValueClock
        #    - eventType is Updated
        #    - timestamp <The intervals between the timestamps of the received Meter Value
        #      messages equals the configured clock-aligned Meter Values interval>.
        #    - sampledValue.context is Sample.Clock
        #    Note(s):
        #    - This step will be executed every <Configured clock-aligned Meter Values interval>
        #    - The Test System will end the testcase after the <Configured transaction duration>
        #      is reached.
        # 4. The CSMS responds with a TransactionEventResponse
        await cp.call(call.TransactionEvent(
            event_type='Updated',
            timestamp=utc_iso(moment),
            trigger_reason='MeterValueClock',
            seq_no=cp.next_seq_no(),
            transaction_info={'transaction_id': transaction_id},
            meter_value=[transaction_meter.meter_value('Sample.Clock', at=moment)],
        ))
        if moment >= end_of_test:
            break

    start_task.cancel()
