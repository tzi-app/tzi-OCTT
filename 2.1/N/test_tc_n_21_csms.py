"""
Test case name      Alert Event - HardWiredMonitor
Test case Id        TC_N_21_CSMS
Use case Id(s)      N07
Requirement(s)      N07.FR.03

Requirement Details:
    N07.FR.03: The CSMS SHALL respond with an empty NotifyEventResponse.
        Precondition: When the CSMS receives an NotifyEventRequest
System under test   CSMS

Description         Charging Station sends an NotifyEventRequest for a HardWiredMonitor.

Purpose             To test that the CSMS is able to handle a HardWiredMonitor.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Test System sends NotifyEventRequest message with
    - eventNotificationType = HardWiredMonitor
2. CSMS returns NotifyEventResponse message.

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
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_21(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Test System sends NotifyEventRequest message with
    #    - eventNotificationType = HardWiredMonitor
    # 2. CSMS returns NotifyEventResponse message.
    response = await cp.send_event(
        {'name': 'Connector', 'evse': {'id': CONFIGURED_EVSE_ID, 'connector_id': CONFIGURED_CONNECTOR_ID}},
        'Problem', 'true', trigger='Alerting', event_notification_type='HardWiredMonitor')
    # NotifyEventResponse with empty body.
    assert response.payload == {}, f"Expected a NotifyEventResponse with empty body, got {response.payload}"

    start_task.cancel()
