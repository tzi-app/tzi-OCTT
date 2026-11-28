"""
Test case name      Set Variable Monitoring - Periodic event
Test case Id        TC_N_24_CSMS
Use case Id(s)      N08
Requirement(s)      N08.FR.02

Requirement Details:
    N08.FR.02: The CSMS SHALL respond with an empty NotifyEventResponse.
        Precondition: When the CSMS receives an NotifyEventRequest
System under test   CSMS

Description         Charging Station sends a periodic NotifyEventRequest.

Purpose             To test that CSMS returns a NotifyEventResponse.
                    Note: this is identical to TC_N_21_CSMS, only with a periodic event.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Tester makes Test System send a NotifyEventRequest message.

1. Test System sends NotifyEventRequest message.
2. CSMS returns NotifyEventResponse message.

Note(s):
- Step 1 and 2 will be repeated n times

Tool validations
* Step 2:
    Message: NotifyEventResponse with empty body.

Post scenario validations:
    N/A
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])

# How many times the periodic event is sent: the n of the scenario
NUMBER_OF_EVENTS = 3


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_24(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Tester makes Test System send a NotifyEventRequest message.
    # 1. Test System sends NotifyEventRequest message.
    # 2. CSMS returns NotifyEventResponse message.
    # Note(s): Step 1 and 2 will be repeated n times
    # The event is the one of a periodic monitor: the power of the EVSE at that moment.
    for index in range(NUMBER_OF_EVENTS):
        response = await cp.send_event(
            {'name': 'EVSE', 'evse': {'id': CONFIGURED_EVSE_ID}}, 'Power', str(1000.0 * index),
            trigger='Periodic', event_notification_type='CustomMonitor', variable_monitoring_id=1)
        # NotifyEventResponse with empty body.
        assert response.payload == {}, \
            f"Expected a NotifyEventResponse with empty body, got {response.payload}"
        await asyncio.sleep(1)

    start_task.cancel()
