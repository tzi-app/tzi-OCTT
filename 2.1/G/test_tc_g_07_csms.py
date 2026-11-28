"""
Test case name      Change Availability Connector - Operative to inoperative
Test case Id        TC_G_07_CSMS
Use case Id(s)      G03
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers how the CSMS requests the Charging Station to change the
                    availability of one of the Connectors of one EVSE from Operative to Inoperative. A
                    Connector is considered Operative in any status other than Faulted and Unavailable.

Purpose             To verify if the CSMS is able to perform the change availability mechanism as described at
                    the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to change the availability of a Connector to Inoperative.

1. The CSMS sends a ChangeAvailabilityRequest
2. The Test System responds with a ChangeAvailabilityResponse with status Accepted
3. The Test System notifies the CSMS about the current state of the connector.
    Message: StatusNotificationRequest
    - connectorStatus Unavailable
    - evseId <Configured evseId>
    - connectorId <Configured connectorId>
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Unavailable"
    - component.name "Connector"
    - component.evse.id <Configured evseId>
    - component.evse.connectorid <Configured connectorId>
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message ChangeAvailabilityRequest
    - operationalStatus Inoperative
    - evse.id <Configured evseId>
    - evse.connectorId <Configured connectorId>

Post scenario validations:
    N/a
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
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_g_07(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to change the availability of a Connector to Inoperative.
    # 1. The CSMS sends a ChangeAvailabilityRequest
    # 2. The Test System responds with a ChangeAvailabilityResponse with status Accepted
    cp.set_response('ChangeAvailability', status='Accepted')
    request = await cp.wait_for_request(
        'ChangeAvailability',
        manual_action=send_call(BASIC_AUTH_CP, 'ChangeAvailability', {
            'operationalStatus': 'Inoperative',
            'evse': {'id': CONFIGURED_EVSE_ID, 'connectorId': CONFIGURED_CONNECTOR_ID},
        }))
    assert request.operational_status == 'Inoperative', \
        f"Expected ChangeAvailabilityRequest.operationalStatus Inoperative, got {request.operational_status}"
    assert request.evse is not None and request.evse.id == CONFIGURED_EVSE_ID, \
        f"Expected ChangeAvailabilityRequest.evse.id {CONFIGURED_EVSE_ID}, got {request.evse}"
    assert request.evse.connector_id == CONFIGURED_CONNECTOR_ID, \
        f"Expected ChangeAvailabilityRequest.evse.connectorId {CONFIGURED_CONNECTOR_ID}, " \
        f"got {request.evse.connector_id}"

    # 3. The Test System notifies the CSMS about the current state of the connector.
    #    Message: StatusNotificationRequest
    #    - connectorStatus Unavailable
    #    - evseId <Configured evseId>
    #    - connectorId <Configured connectorId>
    #    Message: NotifyEventRequest
    #    - trigger Delta
    #    - actualValue "Unavailable"
    #    - component.name "Connector"
    #    - component.evse.id <Configured evseId>
    #    - component.evse.connectorid <Configured connectorId>
    #    - variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    await cp.send_connector_status('Unavailable', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    start_task.cancel()
