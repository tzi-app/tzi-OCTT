"""
Test case name      Offline Start Transaction - Valid IdTag
Test case Id        TC_037_1_CSMS
OCPP version        1.6J
Profile             Core
Section             3.12. Core Profile - Offline behavior Non-Happy Flow
                    3.12.1. Offline Start Transaction - Valid IdTag
Document ref        Table 150 (Page 131/176)

Description         This scenario is used to start a transaction, while being offline.

Purpose             To test if the Central System can handle when a Charge Point starts a
                    transaction, while being offline and queues transaction-related messages,
                    after restoring the connection.

System under test   Central System (SUT)

Prerequisite(s)     n/a

Configuration State(s):
    n/a

Memory State(s):
    n/a

Reusable State(s):
    n/a

Test Scenario
    [Remove connectivity between Charge Point and Central System.]
    [EV Driver starts offline a transaction with a valid idTag.]
    [Restore connectivity between Charge Point and Central System.]

1. The Charge Point sends a StartTransaction.req to the Central System.
    - connectorId: <Configured connectorId>
    - idTag: <Configured valid idTag>
    - meterStart: <meter value at transaction start>
    - timestamp: <timestamp of transaction start (while offline)>
2. The Central System responds with a StartTransaction.conf.
3. The Charge Point sends a StatusNotification.req to the Central System.
    - connectorId: <Configured connectorId>
    - errorCode: NoError
    - status: Charging
4. The Central System responds with a StatusNotification.conf.

Tool validations
* Step 2:
    (Message: StartTransaction.conf)
    idTagInfo.status is Accepted
* Step 3:
    (Message: StatusNotification.req)
    status is Charging

Expected result(s)  n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import AuthorizationStatus, ChargePointStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_037_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: StartTransaction with valid idTag (offline scenario, queued)
    start_response = await cp.send_start_transaction(CONNECTOR_ID, VALID_ID_TAG)
    assert start_response.id_tag_info['status'] == AuthorizationStatus.accepted

    # Step 3-4: StatusNotification(Charging)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.charging)

    start_task.cancel()
