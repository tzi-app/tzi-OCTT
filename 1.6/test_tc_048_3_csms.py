"""
Test case name      Reservation of a Connector - Unavailable
Test case Id        TC_048_3_CSMS
OCPP Version        1.6J
Document Ref        Table 170, pages 145-146/176 (CompliancyTestTool-TestCaseDocument 2025-11)
Section             3.17.1 - Reservation of a Connector
                    NOTE: Section reference is from the OCPP 1.6 specification, not the test case document.

Description         The Central System attempts to reserve a Connector, but the reservation
                    is not made, instead the status Unavailable is returned by the Charge Point.

Purpose             Check whether the Central System can handle messages in case that a
                    reservation cannot be made.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System sends a ChangeAvailability.req to the Charge Point.
   - connectorId: <Configured ConnectorId>
   - type: Inoperative
2. The Charge Point responds with a ChangeAvailability.conf to the Central System.
3. The Charge Point sends a StatusNotification.req to the Central System.
   - status: Unavailable
   - connectorId: same connectorId as in step 1
4. The Central System responds with a StatusNotification.conf to the Charge Point.
5. The Central System sends a ReserveNow.req to the Charge Point.
   - connectorId: same connectorId as in step 1
   - idTag: <Configured Valid IdTag>
   - reservationId: a unique reservation identifier chosen by the Central System
   - expiryDate: a future timestamp
6. The Charge Point responds with a ReserveNow.conf to the Central System.

Tool validations (Charge Point side):
* Step 3:
    Message: StatusNotification.req
    - status is "Unavailable"
    - connectorId equals the connectorId from step 1
* Step 6:
    Message: ReserveNow.conf
    - status is "Unavailable"

Tool validations (Central System side):
* Step 1:
    Message: ChangeAvailability.req
    - connectorId should be <Configured ConnectorId>
    - type is "Inoperative"
* Step 5:
    Message: ReserveNow.req
    - connectorId should be the connectorId from step 1
    - idTag should be <Configured Valid IdTag>

Expected result(s) / behaviour:
    Charge Point (Tool) side: n/a
    Central System (SUT) side:
        The Central System accepts the Reservation message with the not Accepted status.
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
async def test_tc_048_3(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Set CP to respond with Unavailable status for the upcoming ReserveNow
    cp._reserve_now_response_status = ReservationStatus.unavailable

    # Step 1-2: Wait for CSMS to send ChangeAvailability.req → CP responds Accepted
    await asyncio.wait_for(cp._received_change_availability.wait(), timeout=ACTION_TIMEOUT)

    # Step 3-4: CP sends StatusNotification(Unavailable)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.unavailable)

    # Step 5-6: Wait for CSMS to send ReserveNow.req → CP responds Unavailable
    await asyncio.wait_for(cp._received_reserve_now.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reserve_now_data is not None

    start_task.cancel()
