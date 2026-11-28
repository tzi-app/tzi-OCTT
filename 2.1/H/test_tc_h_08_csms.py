"""
Test case name      Reserve an unspecified EVSE - Accepted
Test case Id        TC_H_08_CSMS
Use case Id(s)      H01(S1), H03
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve an unspecified EVSE for a specific IdToken by sending a
                    ReserveNowRequest without an evseId.

Purpose             To verify if the CSMS is able to request the Charging Station to reserve an unspecified
                    EVSE, until the EV Driver with the specified IdToken arrives.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest for an unspecified EVSE.

1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse with status Accepted
3. The Test System notifies the CSMS about the current state of the connector(s) of the configured EVSE
    Message: StatusNotificationRequest
    - with connectorStatus Reserved
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Reserved"
    - component.name "Connector"
    - variable.name "AvailabilityState"
    Note(s):
    - The Test System will execute this step, if it is configured with only one EVSE.
4. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: ReserveNowRequest
    - evseId must be omitted
    - connectorType must be omitted
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import CONFIGURED_NUMBER_OF_EVSES, TziChargePoint21
from reusable_states.booted import booted
from reusable_states.reserved import reserve_now_payload, validate_reserve_now_request
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
async def test_tc_h_08(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger the CSMS to send a ReserveNowRequest for an unspecified EVSE.
    # 1. The CSMS sends a ReserveNowRequest
    # 2. The Test System responds with a ReserveNowResponse with status Accepted
    cp.set_response('ReserveNow', status='Accepted')
    request = await cp.wait_for_request(
        'ReserveNow', manual_action=send_call(BASIC_AUTH_CP, 'ReserveNow', reserve_now_payload()))
    # evseId must be omitted, connectorType must be omitted
    validate_reserve_now_request(request)

    # 3. The Test System notifies the CSMS about the current state of the connector(s) of the
    #    configured EVSE
    #    Message: StatusNotificationRequest - with connectorStatus Reserved
    #    Message: NotifyEventRequest - with trigger Delta, actualValue "Reserved",
    #             component.name "Connector", variable.name "AvailabilityState"
    #    Note(s): The Test System will execute this step, if it is configured with only one EVSE.
    # 4. The CSMS responds accordingly.
    if CONFIGURED_NUMBER_OF_EVSES == 1:
        await cp.send_connector_status('Reserved', evse_id=CONFIGURED_EVSE_ID,
                                       connector_id=CONFIGURED_CONNECTOR_ID)

    start_task.cancel()
