"""
Test case name      Reserve a connector with a specific type - Success
Test case Id        TC_H_15_CSMS
Use case Id(s)      H01(S3), H03
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve an EVSE with a connector with a specific type for a specific
                    IdToken by sending a ReserveNowRequest with a connectorType.

Purpose             To verify if the CSMS is able to request the Charging Station to reserve an EVSE with a
                    connector with a specific type, until the EV Driver with the specified IdToken arrives.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific ConnectorType.

1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse
    With status Accepted
3. The Test System notifies the CSMS about the current state of the connector
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
    - evseId must be omitted
    - connectorType must be <Configured connectorType>
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
CONFIGURED_CONNECTOR_TYPE = os.environ['CONFIGURED_CONNECTOR_TYPE']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_h_15(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific ConnectorType.
    # 1. The CSMS sends a ReserveNowRequest
    # 2. The Test System responds with a ReserveNowResponse With status Accepted
    cp.set_response('ReserveNow', status='Accepted')
    request = await cp.wait_for_request(
        'ReserveNow',
        manual_action=send_call(BASIC_AUTH_CP, 'ReserveNow', reserve_now_payload(
            connector_type=CONFIGURED_CONNECTOR_TYPE)))
    # evseId must be omitted, connectorType must be <Configured connectorType>
    validate_reserve_now_request(request, connector_type=CONFIGURED_CONNECTOR_TYPE)

    # 3. The Test System notifies the CSMS about the current state of the connector
    #    Message: StatusNotificationRequest - with connectorStatus Reserved
    #    Message: NotifyEventRequest - with trigger Delta, actualValue "Reserved",
    #             component.name "Connector", variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    await cp.send_connector_status('Reserved', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    start_task.cancel()
