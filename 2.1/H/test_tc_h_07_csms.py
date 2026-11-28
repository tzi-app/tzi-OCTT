"""
Test case name      Reserve a specific EVSE - Reservation Ended / not used
Test case Id        TC_H_07_CSMS
Use case Id(s)      H01(S2), H04
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve a specific EVSE for a specific IdToken by sending a
                    ReserveNowRequest containing an evseId.

Purpose             To verify if the CSMS is able to handle a reservation that is canceled by the Charging
                    Station, because the EV driver did not arrive before the set expiryDateTime was reached.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific EVSE.

1. The CSMS sends a ReserveNowRequest with
    - expiryDateTime current time + <configured transaction duration>
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
5. The Test System notifies the CSMS about the current state of the connector(s) of the configured EVSE
    Message: StatusNotificationRequest
    - with connectorStatus Available
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
    Note(s):
    - The Test System waits until the provided expiryDateTime from step 1 expires before executing this step.
6. The CSMS responds accordingly.
7. The Test System sends a ReservationStatusUpdateRequest
    With reservationUpdateStatus Expired
    reservationId <id received at step 1>
8. The CSMS responds with a ReservationStatusUpdateResponse

Tool validations
* Step 1:
    Message: ReserveNowRequest
    - evseId must be <Configured evseId>
    - connectorType must be omitted
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

Post scenario validations:
    N/a
"""

import asyncio
import os
from datetime import datetime, timezone

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
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_h_07(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific EVSE.
    # 1. The CSMS sends a ReserveNowRequest with
    #    - expiryDateTime current time + <configured transaction duration>
    # 2. The Test System responds with a ReserveNowResponse With status Accepted
    cp.set_response('ReserveNow', status='Accepted')
    request = await cp.wait_for_request(
        'ReserveNow',
        manual_action=send_call(BASIC_AUTH_CP, 'ReserveNow', reserve_now_payload(
            evse_id=CONFIGURED_EVSE_ID, expires_in=TRANSACTION_DURATION)))
    validate_reserve_now_request(request, evse_id=CONFIGURED_EVSE_ID)

    # 3. The Test System notifies the CSMS about the current state of the connector(s) of the
    #    configured EVSE
    #    Message: StatusNotificationRequest - with connectorStatus Reserved
    #    Message: NotifyEventRequest - with trigger Delta, actualValue "Reserved",
    #             component.name "Connector", variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    await cp.send_connector_status('Reserved', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    # 5. The Test System notifies the CSMS about the current state of the connector(s) of the
    #    configured EVSE
    #    Message: StatusNotificationRequest - with connectorStatus Available
    #    Message: NotifyEventRequest - with trigger Delta, actualValue "Available",
    #             component.name "Connector", variable.name "AvailabilityState"
    #    Note(s): The Test System waits until the provided expiryDateTime from step 1 expires
    #    before executing this step.
    # 6. The CSMS responds accordingly.
    expiry = datetime.fromisoformat(request.expiry_date_time.replace('Z', '+00:00'))
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    await asyncio.sleep(max(0.0, (expiry - datetime.now(timezone.utc)).total_seconds()))
    await cp.send_connector_status('Available', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    # 7. The Test System sends a ReservationStatusUpdateRequest
    #    With reservationUpdateStatus Expired
    #    reservationId <id received at step 1>
    # 8. The CSMS responds with a ReservationStatusUpdateResponse
    await cp.send_reservation_status_update(request.id, 'Expired')

    start_task.cancel()
