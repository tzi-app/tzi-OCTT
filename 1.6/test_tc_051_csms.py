"""
Test case name      Cancel Reservation
Test case Id        TC_051_CSMS
OCPP Version        1.6J
Section             3.17.3 - Cancel Reservation
Document ref        CompliancyTestTool-TestCaseDocument, Table 173, pages 147-148/176

Description         The Central System cancels an existing, not expired reservation.

Purpose             Check whether the Central System can trigger the Charge Point to
                    cancel a reservation.
                    (Note: document has typo "trigger to Charge Point" - corrected here)

Prerequisite(s)     The Central System supports the Reservation feature profile.

Test Scenario
1. The Central System sends a ReserveNow.req to the Charge Point.
   - connectorId: a specific connector (not 0)
   - idTag: <Configured Valid IdTag>
   - reservationId: a unique reservation identifier chosen by the Central System
   - expiryDate: a future timestamp
2. The Charge Point responds with a ReserveNow.conf to the Central System.
3. The Charge Point sends a StatusNotification.req to the Central System.
4. The Central System responds with a StatusNotification.conf to the Charge Point.
5. The Central System sends a CancelReservation.req to the Charge Point.
   - reservationId: the same reservationId as in step 1
6. The Charge Point responds with a CancelReservation.conf to the Central System.
7. The Charge Point sends a StatusNotification.req to the Central System.
8. The Central System responds with a StatusNotification.conf to the Charge Point.

Tool validations (Charge Point side):
* Step 2:
    Message: ReserveNow.conf
    - status is "Accepted"
* Step 3:
    Message: StatusNotification.req
    - status is "Reserved"
* Step 6:
    Message: CancelReservation.conf
    - status is "Accepted"
* Step 7:
    Message: StatusNotification.req
    - status is "Available"

Tool validations (Central System side):
* Step 1:
    Message: ReserveNow.req
    - connectorId does not equal 0
* Step 5:
    Message: CancelReservation.req
    - reservationId matches the reservationId from step 1

Expected result(s):
    The Charge Point handles the reservation correctly, cancelling only the
    reservation with the right reservationId. After cancellation the connector
    transitions back to Available status.
    The Central System processes the response from the Charge Point to the
    cancel reservation message.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_051(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ReserveNow.req → CP responds Accepted
    await asyncio.wait_for(cp._received_reserve_now.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reserve_now_data is not None
    assert cp._reserve_now_data['connector_id'] != 0
    reservation_id = cp._reserve_now_data['reservation_id']

    # Step 3-4: CP sends StatusNotification(Reserved)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.reserved)

    # Step 5-6: Wait for CSMS to send CancelReservation.req → CP responds Accepted
    await asyncio.wait_for(cp._received_cancel_reservation.wait(), timeout=ACTION_TIMEOUT)
    # Verify the cancellation targets the same reservation
    assert cp._cancel_reservation_id == reservation_id

    # Step 7-8: CP sends StatusNotification(Available)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.available)

    start_task.cancel()
