"""
Test case name      Regular Charging Session - Plugin First
Test case Id        TC_003_CSMS
OCPP Version        1.6j
Chapter             3.2.1 - Start Charging Session
System under test   Central System
PDF Reference       CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, pages 110-111, Table 123
HTML Reference      CompliancyTestTool-TestCaseDocument.html, page 110 of 176

Description         This scenario is used to start a Charging session.

Purpose             To test if the Central System can handle when the Charge Point starts a Charging
                    Session when first doing plugin cable.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
    Charge Point (Tool)                                     Central System (SUT)
    -----------------------------------------------         -----------------------------------------------
    [EV driver plugs in the cable.]
    1. The Charge Point sends a StatusNotification.req       2. The Central System responds with a
                                                                StatusNotification.conf

    [EV driver presents identification.]
    3. The Charge Point sends an Authorize.req               4. The Central System responds with an
                                                                Authorize.conf

    5. The Charge Point sends a StartTransaction.req         6. The Central System responds with a
                                                                StartTransaction.conf

    7. The Charge Point sends a StatusNotification.req       8. The Central System responds with a
                                                                StatusNotification.conf

Tool Validations
    * Step 1:
      (Message: StatusNotification.req)
      - status is Preparing

    * Step 4:
      (Message: Authorize.conf)
      - idTagInfo.status is Accepted

    * Step 6:
      (Message: StartTransaction.conf)
      - idTagInfo.status is Accepted

    * Step 7:
      (Message: StatusNotification.req)
      - status is Charging

Expected Result(s)  n/a
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
async def test_tc_003(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: EV driver plugs in cable → StatusNotification(Preparing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.preparing)

    # Step 3-4: EV driver presents identification → Authorize
    auth_response = await cp.send_authorize(VALID_ID_TAG)
    assert auth_response.id_tag_info['status'] == AuthorizationStatus.accepted

    # Step 5-6: StartTransaction
    start_response = await cp.send_start_transaction(CONNECTOR_ID, VALID_ID_TAG)
    assert start_response.id_tag_info['status'] == AuthorizationStatus.accepted
    assert start_response.transaction_id is not None

    # Step 7-8: StatusNotification(Charging)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.charging)

    start_task.cancel()
