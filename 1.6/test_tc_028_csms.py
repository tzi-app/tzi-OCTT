"""
Test case name      Remote Stop Transaction – Rejected
Test case Id        TC_028_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.9.2 - Core Profile - Remote Actions Non-Happy Flow
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument, Table 146, Page 128/176

Description         This scenario is used to reject a RemoteStopTransaction.req,
                    when an unknown transactionId is given.

Purpose             To test if the Central System can handle when a Charge Point rejects
                    a RemoteStopTransaction.req, when an unknown transactionId is given.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): Charging

Test Scenario
    1. The Central System sends a RemoteStopTransaction.req
    2. The Charge Point responds with a RemoteStopTransaction.conf

Tool Validations
    * Step 2 (RemoteStopTransaction.conf): status MUST be "Rejected"

Note: The docstring and mermaid diagram state the CSMS should send an "unknown"
      transactionId (i.e. one that doesn't match the active transaction). However,
      the Tool Validations only require checking the response status, not the request
      content. The test therefore does not assert that the received transactionId
      differs from the actual one — this is a CSMS-side behavior that the spec
      does not explicitly require the tool to validate.

Expected Result     n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import RemoteStartStopStatus

from charge_point import TziChargePoint16
from reusable_states import booted, authorized, charging
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_028(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # CP will reject remote stop (unknown transactionId)
    cp._remote_stop_response_status = RemoteStartStopStatus.rejected
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: Reusable State Charging (Booted → Authorized → Charging)
    await booted(cp)
    await authorized(cp, VALID_ID_TAG)
    await charging(cp, VALID_ID_TAG, CONNECTOR_ID)

    # Step 1-2: Wait for CSMS to send RemoteStopTransaction.req → CP responds Rejected
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'remote-stop-transaction', {'transactionId': 999999}))
    await asyncio.wait_for(cp._received_remote_stop.wait(), timeout=ACTION_TIMEOUT)

    start_task.cancel()
