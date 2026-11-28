"""
Test case name      Change Availability Charging Station - Operative to inoperative
Test case Id        TC_G_05_CSMS
Use case Id(s)      G04
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how the CSMS requests the Charging Station to change the
                    availability from operative to inoperative.
                    A Charging Station is considered Operative when it is charging or ready for charging.
                    A Charging Station is considered Inoperative when it does not allow any charging.

Purpose             To verify if the CSMS is able to perform the change availability mechanism as described at
                    the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to change the availability of the Charging Station to Inoperative.

1. The CSMS sends a ChangeAvailabilityRequest
2. The Test System responds with a ChangeAvailabilityResponse with status Accepted
3. The Test System notifies the CSMS about the current state of all connectors
    Message: StatusNotificationRequest
    - connectorStatus Unavailable
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Unavailable"
    - component.name "Connector"
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message ChangeAvailabilityRequest
    - operationalStatus Inoperative
    - evseId omit
    - connectorId omit

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_g_05(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to change the availability of the Charging Station to
    #                Inoperative.
    # 1. The CSMS sends a ChangeAvailabilityRequest
    # 2. The Test System responds with a ChangeAvailabilityResponse with status Accepted
    cp.set_response('ChangeAvailability', status='Accepted')
    request = await cp.wait_for_request(
        'ChangeAvailability',
        manual_action=send_call(BASIC_AUTH_CP, 'ChangeAvailability', {'operationalStatus': 'Inoperative'}))
    assert request.operational_status == 'Inoperative', \
        f"Expected ChangeAvailabilityRequest.operationalStatus Inoperative, got {request.operational_status}"
    # evseId omit, connectorId omit
    assert request.evse is None, f"ChangeAvailabilityRequest.evse must be omitted, got {request.evse}"

    # 3. The Test System notifies the CSMS about the current state of all connectors
    #    Message: StatusNotificationRequest
    #    - connectorStatus Unavailable
    #    Message: NotifyEventRequest
    #    - trigger Delta
    #    - actualValue "Unavailable"
    #    - component.name "Connector"
    #    - variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    await cp.send_all_connectors_status('Unavailable')

    start_task.cancel()
