"""
Test case name      Reservation of a Connector - Occupied
Test case Id        TC_048_2_CSMS
OCPP Version        1.6J
Section             3.17.1 - Reservation of a Connector
                    NOTE: OCTT document uses section 2.21.1 (to be verified)
Document Reference  Table 169, pages 144-145 of CompliancyTestTool-TestCaseDocument (2025-11)

Description         The Central System attempts to reserve a Connector, but the reservation
                    is not made, instead the status Occupied is returned by the Charge Point.

Purpose             Check whether the Central System can handle messages in case that a
                    reservation cannot be made.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
   [EV driver plugs in cable]
1. The Charge Point sends a StatusNotification.req to the Central System.
   - status: Preparing
   - connectorId: <Configured ConnectorId>
2. The Central System responds with a StatusNotification.conf to the Charge Point.
3. The Central System sends a ReserveNow.req to the Charge Point.
   - connectorId: same connectorId as in step 1
   - idTag: <Configured Valid IdTag>
   - reservationId: a unique reservation identifier chosen by the Central System
     NOTE: not explicitly listed in OCTT tool validations, inferred from OCPP spec (to be verified)
   - expiryDate: a future timestamp
     NOTE: not explicitly listed in OCTT tool validations, inferred from OCPP spec (to be verified)
4. The Charge Point responds with a ReserveNow.conf to the Central System.

Tool validations (Charge Point side):
* Step 1:
    Message: StatusNotification.req
    - status is "Preparing"
    - connectorId is <Configured ConnectorId>
* Step 4:
    Message: ReserveNow.conf
    - status is "Occupied"

Tool validations (Central System side):
* Step 3:
    Message: ReserveNow.req
    - connectorId should be the connectorId from step 1
    - idTag should be <Configured Valid IdTag>

Expected result(s):
    CP: n/a
    CS: The Central System accepts the Reservation message with the not Accepted status.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus, ReservationStatus

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
async def test_tc_048_2(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Set CP to respond with Occupied status for the upcoming ReserveNow
    cp._reserve_now_response_status = ReservationStatus.occupied

    # Step 1-2: EV driver plugs in cable → CP sends StatusNotification(Preparing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.preparing)

    # Step 3-4: Wait for CSMS to send ReserveNow.req → CP responds Occupied
    await asyncio.wait_for(cp._received_reserve_now.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reserve_now_data is not None

    start_task.cancel()
