"""
Test case name      Unlock Connector – Unlock Failure
Test case Id        TC_030_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.10. Core Profile - Unlocking Non-happy flow
                    3.10.1. Unlock Connector – Unlock Failure
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument-CSMS-Section3, Table 147, Page 129/176

Description         This scenario is used to report a connector lock failure.

Purpose             To test if the Central System is able to handle a report of a connector
                    lock failure.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. The Central System sends an UnlockConnector.req
    2. The Charge Point responds with an UnlockConnector.conf

Tool Validations
    * Step 2 (UnlockConnector.conf): status MUST be "UnlockFailed"

Expected Result     n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import UnlockStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_030(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # CP reports unlock failure
    cp._unlock_response_status = UnlockStatus.unlock_failed
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send UnlockConnector.req → CP responds UnlockFailed
    await asyncio.wait_for(cp._received_unlock_connector.wait(), timeout=ACTION_TIMEOUT)
    assert cp._unlock_connector_id is not None

    start_task.cancel()
