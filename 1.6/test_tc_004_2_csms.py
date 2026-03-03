"""
Test case name      Regular Charging Session – Identification First - ConnectionTimeOut
Test case Id        TC_004_2_CSMS
OCPP Version        1.6j
Document Reference  Table 125, pages 111-112/176 (CompliancyTestTool-TestCaseDocument, 2025-11)
Chapter             3.2.3
System under test   Central System

Description         This scenario is used to make a connector available when it is not used.

Purpose             To test if the Central System can handle when the Charge Point sets the
                    connector back to Available, when the connectionTimeOut is reached.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      Authorized (Table 200, page 173/176)
        Definition: CP sends Authorize.req with idTag = <Configured Valid IdTag>,
        CS responds with Authorize.conf where idTagInfo.status should be Accepted.

Test Scenario
1. The Charge Point sends a StatusNotification.req
2. The Central System responds with a StatusNotification.conf
   [After the configured connectionTimeOut has expired.]
3. The Charge Point sends a StatusNotification.req
4. The Central System responds with a StatusNotification.conf

Tool Validations
    * Step 1 (Message: StatusNotification.req):
        - status is Preparing
    * Step 3 (Message: StatusNotification.req):
        - status is Available

Expected Result(s)  n/a

OCPP 1.6 Messages Used:
    - StatusNotification.req / StatusNotification.conf

Configuration Keys:
    - ConnectionTimeOut (Integer, seconds): The time in seconds after which the Charge Point
      will revert to Available if no cable is plugged in after authorization.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus

from charge_point import TziChargePoint16
from reusable_states import authorized
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_004_2(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: Reusable State Authorized (Table 200)
    await authorized(cp, VALID_ID_TAG)

    # Step 1-2: StatusNotification(Preparing) - connector waiting for cable
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.preparing)

    # [connectionTimeOut expires - no cable plugged in]

    # Step 3-4: StatusNotification(Available) - connector reverts
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.available)

    start_task.cancel()
