"""
Test case name      Clock-aligned Meter Values - No transaction ongoing
Test case Id        TC_J_01_CSMS
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
                    Values, when there is no ongoing transaction.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System notifies the CSMS about its measured Meter Values.
    Message: MeterValuesRequest
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      _<Configured clock-aligned Meter Values interval>.
    - sampledValue.context is Sample.Clock
    Message: NotifyEventRequest
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      _<Configured clock-aligned Meter Values interval>.
    - trigger is Periodic
    - component.name is FiscalMetering

    Note(s):
    - This step will be executed every _<Configured clock-aligned Meter Values interval>
    - This step will be executed for evseId=0 and all configured EVSE.
    - The Test System will end the testcase after it has send three Meter Value messages.
2. The CSMS responds accordingly.

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import CONFIGURED_NUMBER_OF_EVSES, TziChargePoint21
from metering import EnergyMeter, ticks, utc_iso
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CLOCK_ALIGNED_METER_VALUES_INTERVAL = int(os.environ['CLOCK_ALIGNED_METER_VALUES_INTERVAL'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_j_01(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The Test System notifies the CSMS about its measured Meter Values.
    #    Message: MeterValuesRequest
    #    - timestamp <The intervals between the timestamps of the received Meter Value messages
    #      equals the <Configured clock-aligned Meter Values interval>.
    #    - sampledValue.context is Sample.Clock
    #    Message: NotifyEventRequest
    #    - timestamp <The intervals between the timestamps of the received Meter Value messages
    #      equals the <Configured clock-aligned Meter Values interval>.
    #    - trigger is Periodic
    #    - component.name is FiscalMetering
    #    Note(s):
    #    - This step will be executed every <Configured clock-aligned Meter Values interval>
    #    - This step will be executed for evseId=0 and all configured EVSE.
    #    - The Test System will end the testcase after it has send three Meter Value messages.
    # 2. The CSMS responds accordingly.
    #
    # No transaction is ongoing: the registers of the meters stand still.
    meters = {evse_id: EnergyMeter() for evse_id in range(0, CONFIGURED_NUMBER_OF_EVSES + 1)}
    times_sent = 0
    async for moment in ticks(CLOCK_ALIGNED_METER_VALUES_INTERVAL, clock_aligned=True):
        for evse_id, meter in meters.items():
            reading = meter.reading(moment)
            await cp.send_meter_values(
                evse_id, [{'value': reading, 'context': 'Sample.Clock'}], timestamp=utc_iso(moment))
            component = {'name': 'FiscalMetering'}
            if evse_id:
                component['evse'] = {'id': evse_id}
            await cp.send_event(component, 'EnergyImportRegister', str(reading), trigger='Periodic',
                                event_notification_type='PreconfiguredMonitor',
                                timestamp=utc_iso(moment))
        times_sent += 1
        if times_sent == 3:
            break

    start_task.cancel()
