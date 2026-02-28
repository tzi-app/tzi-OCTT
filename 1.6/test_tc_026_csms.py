"""
Test case name      Remote Start Charging Session – Rejected
Test case Id        TC_026_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.9.1 - Core Profile - Remote Actions Non-Happy Flow
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument, Table 145, Page 128/176

Description         This scenario is used to reject a RemoteStartTransaction.req.

Purpose             To test if the Central System can handle when a Charge Point rejects
                    a RemoteStartTransaction.req.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    [The CPO remotely requests a start transaction.]
    1. The Central System sends a RemoteStartTransaction.req
    2. The Charge Point responds with a RemoteStartTransaction.conf

Tool Validations
    * Step 2 (RemoteStartTransaction.conf): status is Rejected

Expected Result     n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import RemoteStartStopStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers
from trigger import trigger_v16

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
VALID_ID_TAG = os.environ.get('VALID_ID_TOKEN', 'TEST_TAG')


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_026(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # CP will reject remote start
    cp._remote_start_response_status = RemoteStartStopStatus.rejected
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send RemoteStartTransaction.req → CP responds Rejected
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'remote-start-transaction', {'idTag': VALID_ID_TAG}))
    await asyncio.wait_for(cp._received_remote_start.wait(), timeout=ACTION_TIMEOUT)
    assert cp._remote_start_id_tag is not None

    start_task.cancel()
