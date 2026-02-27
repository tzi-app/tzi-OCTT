"""
Test case name      Reservation of a Connector - Rejected
Test case Id        TC_048_4_CSMS
OCPP Version        1.6J
Section             3.17.1 - Reservation of a Connector
Document ref        Table 171, page 146 (CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf)

Description         The Central System attempts to reserve a Connector, but the reservation
                    is not made, instead the status Rejected is returned by the Charge Point.

Purpose             Check whether the Central System is able to handle messages in case that
                    a reservation cannot be made.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Pre-conditions
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System sends a ReserveNow.req to the Charge Point.
   Note: The doc only validates connectorId and idTag (see Tool validations below),
         but reservationId and expiryDate are required fields per OCPP 1.6 schema.
2. The Charge Point responds with a ReserveNow.conf to the Central System.

Tool validations (Charge Point side):
* Step 2:
    Message: ReserveNow.conf
    - status is Rejected

Tool validations (Central System side):
* Step 1:
    Message: ReserveNow.req
    - connectorId should be <Configured ConnectorId>
    - idTag should be <Configured Valid IdTag>

Expected result(s):
    CP side: n/a
    CS side: The Central System accepts the Reservation message with the not Accepted status.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ReservationStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_048_4(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # CP will respond with Rejected status
    cp._reserve_now_response_status = ReservationStatus.rejected
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ReserveNow.req → CP responds Rejected
    await asyncio.wait_for(cp._received_reserve_now.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reserve_now_data is not None
    assert cp._reserve_now_data['connector_id'] == CONNECTOR_ID
    assert cp._reserve_now_data['id_tag'] == VALID_ID_TAG

    start_task.cancel()
