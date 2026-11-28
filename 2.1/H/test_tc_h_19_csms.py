"""
Test case name      Reserve a specific EVSE - Use a reserved EVSE with GroupId
Test case Id        TC_H_19_CSMS
Use case Id(s)      H01, H03
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve an EVSE for a specific group by sending a ReserveNowRequest
                    containing a groupIdToken.

Purpose             To verify if the CSMS is able to request the Charging Station create a reservation for a
                    specific group, by sending a ReserveNowRequest with a groupIdToken

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest with a groupIdToken for a specific EVSE.

1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse
    With status Accepted
3. The Test System notifies the CSMS about the current state of the connector(s) of the configured EVSE
    Message: StatusNotificationRequest
    - with connectorStatus Reserved
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Reserved"
    - component.name "Connector"
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: ReserveNowRequest
    - evseId must be <Configured evseId>
    - connectorType must be omitted
    - groupIdToken must be provided
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.reserved import reserve_now_payload, validate_reserve_now_request
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
GROUP_ID = os.environ['GROUP_ID']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_h_19(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger the CSMS to send a ReserveNowRequest with a groupIdToken for a
    #                specific EVSE.
    # 1. The CSMS sends a ReserveNowRequest
    # 2. The Test System responds with a ReserveNowResponse With status Accepted
    cp.set_response('ReserveNow', status='Accepted')
    request = await cp.wait_for_request(
        'ReserveNow',
        manual_action=send_call(BASIC_AUTH_CP, 'ReserveNow', reserve_now_payload(
            evse_id=CONFIGURED_EVSE_ID, group_id_token={'idToken': GROUP_ID, 'type': 'Central'})))
    validate_reserve_now_request(request, evse_id=CONFIGURED_EVSE_ID)
    assert request.group_id_token is not None, "ReserveNowRequest.groupIdToken must be provided"

    # 3. The Test System notifies the CSMS about the current state of the connector(s) of the
    #    configured EVSE
    #    Message: StatusNotificationRequest - with connectorStatus Reserved
    #    Message: NotifyEventRequest - with trigger Delta, actualValue "Reserved",
    #             component.name "Connector", variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    await cp.send_connector_status('Reserved', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    start_task.cancel()
