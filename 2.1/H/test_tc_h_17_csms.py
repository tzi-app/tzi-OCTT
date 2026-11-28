"""
Test case name      Cancel reservation of an EVSE - Success
Test case Id        TC_H_17_CSMS
Use case Id(s)      H02
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to cancel a reservation by sending a CancelReservationRequest to the
                    Charging Station.

Purpose             To verify if the CSMS is able to request the Charging Station to cancel a reservation, by
                    sending a CancelReservationRequest

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific EVSE.

1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse
    with status Accepted
3. The Test System notifies the CSMS about the current state of the connector(s) of the configured EVSE
    Message: StatusNotificationRequest
    - with connectorStatus Reserved
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Reserved"
    - component.name "Connector"
    - variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Manual Action: Trigger the CSMS to send a CancelReservationRequest for the reservation created at step 1.

5. The CSMS sends a CancelReservationRequest
6. The Test System responds with a CancelReservationResponse
    With status Accepted
7. The Test System notifies the CSMS about the current state of the connector(s) of the configured EVSE
    Message: StatusNotificationRequest
    - with connectorStatus Available
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
8. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: ReserveNowRequest
    - evseId must be <Configured evseId>
    - connectorType must be omitted
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
* Step 5:
    Message: CancelReservationRequest
    - reservationId must be equal to the id provided at step 1

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


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_h_17(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger the CSMS to send a ReserveNowRequest for a specific EVSE.
    # 1. The CSMS sends a ReserveNowRequest
    # 2. The Test System responds with a ReserveNowResponse with status Accepted
    cp.set_response('ReserveNow', status='Accepted')
    reserve_now = await cp.wait_for_request(
        'ReserveNow',
        manual_action=send_call(BASIC_AUTH_CP, 'ReserveNow', reserve_now_payload(
            evse_id=CONFIGURED_EVSE_ID)))
    validate_reserve_now_request(reserve_now, evse_id=CONFIGURED_EVSE_ID)

    # 3. The Test System notifies the CSMS about the current state of the connector(s) of the
    #    configured EVSE
    #    Message: StatusNotificationRequest - with connectorStatus Reserved
    #    Message: NotifyEventRequest - with trigger Delta, actualValue "Reserved",
    #             component.name "Connector", variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    await cp.send_connector_status('Reserved', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    # Manual Action: Trigger the CSMS to send a CancelReservationRequest for the reservation
    #                created at step 1.
    # 5. The CSMS sends a CancelReservationRequest
    # 6. The Test System responds with a CancelReservationResponse With status Accepted
    cp.set_response('CancelReservation', status='Accepted')
    cancel_reservation = await cp.wait_for_request(
        'CancelReservation',
        manual_action=send_call(BASIC_AUTH_CP, 'CancelReservation', {'reservationId': reserve_now.id}))
    assert cancel_reservation.reservation_id == reserve_now.id, \
        f"Expected CancelReservationRequest.reservationId {reserve_now.id} (the id of step 1), " \
        f"got {cancel_reservation.reservation_id}"

    # 7. The Test System notifies the CSMS about the current state of the connector(s) of the
    #    configured EVSE
    #    Message: StatusNotificationRequest - with connectorStatus Available
    #    Message: NotifyEventRequest - with trigger Delta, actualValue "Available",
    #             component.name "Connector", variable.name "AvailabilityState"
    # 8. The CSMS responds accordingly.
    await cp.send_connector_status('Available', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    start_task.cancel()
