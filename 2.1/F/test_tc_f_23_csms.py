"""
Test case name      Trigger message - StatusNotification - Specific EVSE - Available
Test case Id        TC_F_23_CSMS
Use case Id(s)      F06
Requirement(s)      F06.FR.01, F06.FR.02, F06.FR.13

Requirement Details:
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
    F06.FR.02: The CSMS MAY indicate to which EVSE this request applies.
        Precondition: F06.FR.01. For every such requested message.
    F06.FR.13: The CSMS SHALL set the connectorId field
        Precondition: When sending a TriggerMessageRequest with requestedMessage set to: StatusNotification
        Note: StatusNotification messages can only be sent at connector level.
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to trigger the Charging Station to send a
                    StatusNotificationRequest for a specific available EVSE, using a TriggerMessageRequest.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse with status Accepted
3. The Test System notifies the CSMS about the current state of the connector.
    Message: StatusNotificationRequest
    - connectorStatus Available
    - evseId <Configured evseId>
    - connectorId <Configured connectorId>
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - component.evse.id <Configured evseId>
    - component.evse.connectorid <Configured connectorId>
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage must be StatusNotification
    - evse.id must be <Configured evseId>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import trigger_message
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_f_23(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a TriggerMessageRequest
    #    A StatusNotification is requested for a connector (F06.FR.13).
    # 2. The Test System responds with a TriggerMessageResponse with status Accepted
    cp.set_response('TriggerMessage', status='Accepted')
    request = await cp.wait_for_request(
        'TriggerMessage',
        manual_action=trigger_message(BASIC_AUTH_CP, 'StatusNotification',
                                      evse_id=CONFIGURED_EVSE_ID,
                                      connector_id=CONFIGURED_CONNECTOR_ID))
    assert request.requested_message == 'StatusNotification', \
        f"Expected TriggerMessageRequest.requestedMessage StatusNotification, " \
        f"got {request.requested_message}"
    assert request.evse is not None and request.evse.id == CONFIGURED_EVSE_ID, \
        f"Expected TriggerMessageRequest.evse.id {CONFIGURED_EVSE_ID}, got {request.evse}"

    # 3. The Test System notifies the CSMS about the current state of the connector.
    #    Message: StatusNotificationRequest
    #    - connectorStatus Available
    #    - evseId <Configured evseId>
    #    - connectorId <Configured connectorId>
    #    Message: NotifyEventRequest
    #    - trigger Delta
    #    - actualValue "Available"
    #    - component.name "Connector"
    #    - component.evse.id <Configured evseId>
    #    - component.evse.connectorid <Configured connectorId>
    #    - variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    await cp.send_connector_status('Available', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    start_task.cancel()
