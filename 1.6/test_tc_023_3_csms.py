"""
Test case name      Start Charging Session – Authorize blocked
Test case Id        TC_023_3_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.8.3 - Core Profile - Basic Actions Non-happy flow
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument-CSMS-Section3, Table 143, Page 127/176

Description         This scenario is used to inform the Charge Point that the EV Driver is
                    not Authorized to start a transaction.

Purpose             To test if the Central System is able to provide a blocked response on
                    an Authorize.req.

Prerequisite(s)     The Central System has an idTag in memory with status 'Blocked'.

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    [EV driver presents blocked identification.]
    1. The Charge Point sends an Authorize.req.
    2. The Central System responds with an Authorize.conf.

Tool Validations
    * Step 1 (Authorize.conf):
      - idTagInfo.status is Blocked
      NOTE: Doc says "Step 1" but Authorize.conf is Step 2. Likely a typo in the original OCTT doc.

Expected Result     n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import AuthorizationStatus

from charge_point import TziChargePoint16
from trigger import create_token
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
BLOCKED_ID_TAG = os.environ['BLOCKED_ID_TOKEN']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_023_3(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: ensure the blocked token exists in the CSMS
    await create_token(BLOCKED_ID_TAG, "Blocked")

    # Step 1-2: Authorize with blocked idTag → expect Blocked
    auth_response = await cp.send_authorize(BLOCKED_ID_TAG)
    assert auth_response.id_tag_info['status'] == AuthorizationStatus.blocked

    start_task.cancel()
