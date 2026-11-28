"""
Test case name      Change Availability Connector - With ongoing transaction
Test case Id        TC_G_17_CSMS
Use case Id(s)      G03
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers how the CSMS requests the Charging Station to change the
                    availability of one of the EVSEs from Operative to Inoperative. An EVSE is considered
                    Operative in any status other than Faulted and Unavailable.

Purpose             To verify if the CSMS is able to send a change availability request during a transaction
                    according to the mechanism as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      State is EnergyTransferStarted

Test Scenario
Note(s): Request the CSMS to change the availablitiy of one connector to inoperative

1. The CSMS sends a ChangeAvailabilityRequest
2. The Test System responds with a ChangeAvailabilityResponse with
    status Scheduled

Note(s): Wait for <Configured Transaction Duration>

3. Execute Reusable State StopAuthorized
4. Execute Reusable State EVConnectedPostSession
5. Execute Reusable State EVDisconnected
6. The Test System notifies the CSMS about the current state of all connectors with
    Message: StatusNotificationRequest
    - connectorStatus Unavailable
    - evseId <Configured evseId>
    - connectorId <Configured connectorId>
7. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message ChangeAvailabilityRequest
    - operationalStatus Inoperative
    - evse.id <Configured evseId>
    - evse.connectorId <Configured connectorId>

Post scenario validations:
    - A respond to report the state of a connector has been received for all connectors.
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_connected_post_session import ev_connected_post_session
from reusable_states.ev_disconnected import ev_disconnected
from reusable_states.stop_authorized import stop_authorized
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
async def test_tc_g_17(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    await energy_transfer_started(cp)

    # Note(s): Request the CSMS to change the availablitiy of one connector to inoperative
    # 1. The CSMS sends a ChangeAvailabilityRequest
    # 2. The Test System responds with a ChangeAvailabilityResponse with status Scheduled
    cp.set_response('ChangeAvailability', status='Scheduled')
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

    # Note(s): Wait for <Configured Transaction Duration>
    # 3. Execute Reusable State StopAuthorized (which is where the tool waits for the
    #    <Configured Transaction Duration>)
    await stop_authorized(cp)

    # 4. Execute Reusable State EVConnectedPostSession
    await ev_connected_post_session(cp)

    # 5. Execute Reusable State EVDisconnected
    await ev_disconnected(cp)

    # 6. The Test System notifies the CSMS about the current state of all connectors with
    #    Message: StatusNotificationRequest
    #    - connectorStatus Unavailable
    #    - evseId <Configured evseId>
    #    - connectorId <Configured connectorId>
    # 7. The CSMS responds accordingly: a response to the report of the state of a connector has
    #    been received for all connectors.
    await cp.send_status_notification(CONFIGURED_CONNECTOR_ID, 'Unavailable', evse_id=CONFIGURED_EVSE_ID)

    start_task.cancel()
