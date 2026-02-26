"""
Test case name      Cancel Reservation - Rejected
Test case Id        TC_052_CSMS
OCPP Version        1.6J
Section             3.17.3 - Cancel Reservation
Document ref        OCPP Compliancy Testing Tool - TestCaseDocument (2025-11),
                    Table 174, page 148/176

Description         The Central System tries to cancel reservation, but this request
                    is rejected by the Charge Point.

Purpose             Check whether the Central System can handle messages in case cancelling
                    a reservation is rejected by the Charge Point.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
   [Manual Action: Reserve a connector on the Charge Point]
1. The Central System sends a ReserveNow.req to the Charge Point.
   - connectorId: <Configured ConnectorId>
   - idTag: <Configured Valid IdTag>
   - reservationId: a unique reservation identifier chosen by the Central System
   - expiryDate: a future timestamp
   NOTE: Parameters above are not explicitly listed in the CSMS test case document;
   they are standard OCPP 1.6 ReserveNow.req fields (to be verified later).
2. The Charge Point responds with a ReserveNow.conf to the Central System.
3. The Charge Point sends a StatusNotification.req to the Central System.
4. The Central System responds with a StatusNotification.conf to the Charge Point.

   [Manual Action: Cancel the reservation on the Charge Point]
   (The reservation is cancelled locally on the Charge Point so that the
    CancelReservation.req from the Central System will find no matching reservation.)

5. The Central System sends a CancelReservation.req to the Charge Point.
   - reservationId: a reservation identifier (which no longer exists on the Charge Point)
6. The Charge Point responds with a CancelReservation.conf to the Central System.

Tool validations (Charge Point side):
* Step 2:
    Message: ReserveNow.conf
    - status is "Accepted"
* Step 3:
    Message: StatusNotification.req
    - status is "Reserved"
* Step 6:
    Message: CancelReservation.conf
    - status is "Rejected"

Tool validations (Central System side):
    (No specific Central System validations defined in the document)

Expected result(s):
    The Charge Point rejects the reservationId and does not cancel any reservation.
    The Central System processes the rejection from the Charge Point to the
    cancel reservation message.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import CancelReservationStatus, ChargePointStatus

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
async def test_tc_052(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ReserveNow.req → CP responds Accepted
    await asyncio.wait_for(cp._received_reserve_now.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reserve_now_data is not None

    # Step 3-4: CP sends StatusNotification(Reserved)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.reserved)

    # Set CP to reject the upcoming CancelReservation
    cp._cancel_reservation_response_status = CancelReservationStatus.rejected

    # Step 5-6: Wait for CSMS to send CancelReservation.req → CP responds Rejected
    await asyncio.wait_for(cp._received_cancel_reservation.wait(), timeout=ACTION_TIMEOUT)
    assert cp._cancel_reservation_id is not None

    start_task.cancel()
