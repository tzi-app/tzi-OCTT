"""
Test case name      Regular Start Charging Session – Cached Id
Test case Id        TC_007_CSMS
OCPP version        1.6J
Chapter             3.3 Cache (3.3.1)
Doc reference       CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, Table 127, Section 3.3.1, p.113

System under test   Central System

Description         This scenario is used to start a transaction with an id stored in the Authorization cache.

Purpose             To test if the Central System is able to handle a Charge Point starting a transaction with an id
                    which is stored in the Authorization cache.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    [EV driver plugs in the cable.]
    1. The Charge Point sends a StatusNotification.req.
    2. The Central System responds with a StatusNotification.conf.
    [EV driver presents identification.]
    3. The Charge Point sends a StartTransaction.req.
    4. The Central System responds with a StartTransaction.conf.
    5. The Charge Point sends a StatusNotification.req.
    6. The Central System responds with a StatusNotification.conf.

Tool validation(s)
    * Step 1 (Charge Point / Tool side):
        (Message: StatusNotification.req)
        - status is Preparing
    * Step 4 (Central System / SUT side):
        (Message: StartTransaction.conf)
        - idTagInfo.status is Accepted
    * Step 5 (Charge Point / Tool side):
        (Message: StatusNotification.req)
        - status is Charging

Expected result(s) n/a
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
async def test_tc_007(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: EV driver plugs in cable → StatusNotification(Preparing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.preparing)

    # Step 3-4: StartTransaction with cached idTag (no prior Authorize.req)
    start_response = await cp.send_start_transaction(CONNECTOR_ID, VALID_ID_TAG)
    assert start_response.id_tag_info['status'] == AuthorizationStatus.accepted
    assert start_response.transaction_id is not None

    # Step 5-6: StatusNotification(Charging)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.charging)

    start_task.cancel()
