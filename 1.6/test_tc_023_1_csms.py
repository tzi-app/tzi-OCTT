"""
Test case name      Start Charging Session – Authorize invalid
Test case Id        TC_023_1_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.8.1 - Core Profile - Basic Actions Non-happy flow
System under test   Central System (CSMS)
Document ref        Table 141, Page 126/176, Section 3.8.1
                    (CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, 2025-11)

Description         This scenario is used to inform the Charge Point that the EV Driver is
                    not Authorized to start a transaction.

Purpose             To test if the Central System is able to provide an invalid response on
                    an Authorize.req.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    [EV driver presents invalid identification.]
    1. The Charge Point sends an Authorize.req.
    2. The Central System responds with an Authorize.conf.

Tool Validations (Central System SUT side)
    * Step 1 (Message: Authorize.conf):
      - idTagInfo.status is Invalid

Expected Result     n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import AuthorizationStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
INVALID_ID_TAG = os.environ['INVALID_ID_TOKEN']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_023_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Authorize with invalid idTag → expect Invalid
    auth_response = await cp.send_authorize(INVALID_ID_TAG)
    assert auth_response.id_tag_info['status'] == AuthorizationStatus.invalid

    start_task.cancel()
