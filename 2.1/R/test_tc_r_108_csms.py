"""
Test case name      Charging station reporting a DER event
Test case Id        TC_R_108_CSMS
Use case Id(s)      R05
Requirement(s)      N/a
System under test   CSMS

Description         Configure a DER Control which will always trigger and halfs the charging rate of the
                    charging profile when a transaction starts, then add onother DER Control to test
                    overriding the previous one. After tha clearing all DER controls to test it reports the
                    alert should be cleared.

Purpose             To check if the CSMS supports receiving DER events.

Prerequisite(s)     CSMS supports DER Control

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Report DER alarm
1. The Test System sends a NotifyDERAlarmRequest with
    - controlType LVMustTrip
    - gridEventFault UnderVoltage
    - alarmEnded false
    - timestamp <Current DateTime>
2. The CSMS responds with a NotifyDERAlarmResponse

Note: The Test System waits 5 seconds

Clear DER alarm
3. The Test System sends a NotifyDERAlarmRequest with
    - controlType LVMustTrip
    - gridEventFault UnderVoltage
    - alarmEnded true
    - timestamp <Current DateTime>
4. The CSMS responds with a NotifyDERAlarmResponse

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
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_r_108(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: CSMS supports DER Control
    # Report DER alarm
    # 1. The Test System sends a NotifyDERAlarmRequest with
    #    - controlType LVMustTrip
    #    - gridEventFault UnderVoltage
    #    - alarmEnded false
    #    - timestamp <Current DateTime>
    # 2. The CSMS responds with a NotifyDERAlarmResponse
    await cp.call(call.NotifyDERAlarm(
        control_type='LVMustTrip', grid_event_fault='UnderVoltage', alarm_ended=False,
        timestamp=utc_now_iso()))

    # Note: The Test System waits 5 seconds
    await asyncio.sleep(5)

    # Clear DER alarm
    # 3. The Test System sends a NotifyDERAlarmRequest with
    #    - controlType LVMustTrip
    #    - gridEventFault UnderVoltage
    #    - alarmEnded true
    #    - timestamp <Current DateTime>
    # 4. The CSMS responds with a NotifyDERAlarmResponse
    await cp.call(call.NotifyDERAlarm(
        control_type='LVMustTrip', grid_event_fault='UnderVoltage', alarm_ended=True,
        timestamp=utc_now_iso()))

    start_task.cancel()
