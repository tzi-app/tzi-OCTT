"""
Test case name      Reservation of a Connector - Expire
Test case Id        TC_047_CSMS
OCPP Version        1.6J
Section             3.17.1 - Reservation of a Connector
Document ref        Table 167, Page 143/176 - OCPP Compliancy Testing Tool TestCaseDocument (2025-11)

Description         A Connector is reserved, a charging transaction could take place,
                    but the reservation is not used (in time).

Purpose             Check whether Central System can handle messages when the reservation
                    is not used (in time).

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before:
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System sends a ReserveNow.req to the Charge Point.
   - connectorId: <Configured ConnectorId>
     NOTE: must be > 0, i.e. a specific connector (inferred from OCPP spec, not in test doc - to be verified)
   - idTag: <Configured Valid IdTag>
   - reservationId: a unique reservation identifier chosen by the Central System
   - expiryDate: current time plus <Configured Expiry Date Offset>
2. The Charge Point responds with a ReserveNow.conf to the Central System.
3. The Charge Point sends a StatusNotification.req to the Central System.
4. The Central System responds with a StatusNotification.conf to the Charge Point.

   [EV driver does not arrive at the reserved Connector before the expiry date]

5. The Charge Point sends a StatusNotification.req to the Central System.
6. The Central System responds with a StatusNotification.conf to the Charge Point.

Tool validations (Charge Point side):
* Step 2:
    (Message: ReserveNow.conf)
    - status is Accepted
* Step 3:
    (Message: StatusNotification.req)
    - status is Reserved
* Step 5:
    (Message: StatusNotification.req)
    - status is Available

Tool validations (Central System side):
* Step 1:
    (Message: ReserveNow.req)
    - connectorId should be <Configured ConnectorId>
    - idTag should be <Configured Valid IdTag>
    - expiryDate should be the current time plus <Configured Expiry Date Offset>

Expected result(s) / behaviour:
    n/a (per official test document, both CP and CS sides)
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
async def test_tc_047(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ReserveNow.req → CP responds Accepted
    await asyncio.wait_for(cp._received_reserve_now.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reserve_now_data is not None

    # Step 3-4: CP sends StatusNotification(Reserved)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.reserved)

    # Step 5-6: Reservation expires → CP sends StatusNotification(Available)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.available)

    start_task.cancel()
