"""
Test case name      Reservation of a Connector - Transaction
Test case Id        TC_046_CSMS
OCPP Version        1.6J
Section             3.17.1 - Reservation of a Connector
Document ref        Table 166, Page 143/176 (CompliancyTestTool-TestCaseDocument-CSMS-Section3 2025-11)

Description         A Connector is reserved and a charging transaction takes place.

Purpose             Check whether Central System can trigger a Charge Point to Reserve a Connector.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before:
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System sends a ReserveNow.req to the Charge Point.
   - connectorId is <Configured ConnectorId>
   - idTag is <Configured Valid IdTag>
2. The Charge Point responds with a ReserveNow.conf to the Central System.
3. The Charge Point sends a StatusNotification.req to the Central System.
4. The Central System responds with a StatusNotification.conf to the Charge Point.
5. Execute Reusable State: Charging
   (See Table 201 - Reusable State: Charging, Page 174/176,
    which depends on Table 200 - Reusable State: Authorized, Page 174/176.
    Full sub-flow:
      Authorized (Table 200):
        a. CP sends Authorize.req (idTag: <Configured Valid IdTag>)
        b. CS responds with Authorize.conf (idTagInfo.status should be Accepted)
      Charging (Table 201):
        c. CP sends StatusNotification.req (status: Preparing, connectorId: <Configured ConnectorId>)
        d. CS responds with StatusNotification.conf
        e. CP sends StartTransaction.req (idTag: <Configured Valid IdTag>,
           connectorId: <Configured ConnectorId>)
        f. CS responds with StartTransaction.conf (idTagInfo.status should be Accepted)
        g. CP sends StatusNotification.req (status: Charging, connectorId: <Configured ConnectorId>)
        h. CS responds with StatusNotification.conf)

Tool validations (Charge Point side):
* Step 2:
    Message: ReserveNow.conf
    - The status is Accepted
* Step 3:
    Message: StatusNotification.req
    - The status is Reserved
* Step 5:
    (Reusable State: Charging)
    - The reservationId is the reservationId from step 1

Tool validations (Central System side - SUT):
* Step 1:
    Message: ReserveNow.req
    - The connectorId should be <Configured ConnectorId>
    - The idTag should be <Configured Valid IdTag>

Expected result(s):    n/a (both sides per document)

NOTE (to be fixed later):
    - The document does not explicitly validate reservationId or expiryDate in the ReserveNow.req
      CS-side validations, but these are required fields per OCPP 1.6 spec. Confirm whether the
      OCTT tool validates them implicitly or if additional handling is needed.
    - Step 5 CP-side validation says "The reservationId is the reservationId from step 1" — this
      refers to the StartTransaction.req.reservationId field matching the reservationId sent in
      the ReserveNow.req at step 1.
"""

import asyncio
import os
import pytest
from datetime import datetime, timedelta

from ocpp.v16.enums import AuthorizationStatus, ChargePointStatus

from charge_point import TziChargePoint16
from reusable_states import authorized
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_046(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ReserveNow.req → CP responds Accepted
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'reserve-now', {
        'connectorId': CONNECTOR_ID,
        'expiryDate': (datetime.now() + timedelta(hours=1)).isoformat() + 'Z',
        'idTag': VALID_ID_TAG,
        'reservationId': 1,
    }))
    await asyncio.wait_for(cp._received_reserve_now.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reserve_now_data is not None
    # CS-side validations: ReserveNow.req fields
    assert cp._reserve_now_data['connector_id'] == CONNECTOR_ID
    assert cp._reserve_now_data['id_tag'] == VALID_ID_TAG

    # Capture reservationId from step 1
    reservation_id = cp._reserve_now_data['reservation_id']

    # Step 3-4: CP sends StatusNotification(Reserved)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.reserved)

    # Step 5: Execute Reusable State: Authorized + Charging (with reservationId from step 1)
    await authorized(cp, VALID_ID_TAG)

    # Charging sub-flow (inline to pass reservation_id to StartTransaction)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.preparing)
    start_response = await cp.send_start_transaction(
        CONNECTOR_ID, VALID_ID_TAG, reservation_id=reservation_id,
    )
    assert start_response.id_tag_info['status'] == AuthorizationStatus.accepted
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.charging)

    start_task.cancel()
