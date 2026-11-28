"""
Test case name      Alert Event - Variable monitoring on write only
Test case Id        TC_N_48_CSMS
Use case Id(s)      N07
Requirement(s)      N/a
System under test   CSMS

Description         NotifyEventRequest reports every Component/Variable for which a VariableMonitoring setting
                    was triggered. Only the VariableMonitoring settings that are responsible for triggering an
                    event are included.

Purpose             To verify if the CSMS is able to read a request from a trigger from a variablemonitor
                    which is write only as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The Test System sends a NotifyEventRequest with
    - eventData.actualValue empty
2. The CSMS responds with a NotifyEventResponse.

Tool validations
N/a

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_48(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The Test System sends a NotifyEventRequest with
    #    - eventData.actualValue empty
    #    A monitor on a write-only variable: its value is not reported.
    # 2. The CSMS responds with a NotifyEventResponse.
    await cp.send_event('SecurityCtrlr', 'BasicAuthPassword', '', trigger='Delta',
                        event_notification_type='CustomMonitor', variable_monitoring_id=1)

    start_task.cancel()
