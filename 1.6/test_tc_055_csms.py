"""
Test case name      Trigger Message - Rejected
Test case Id        TC_055_CSMS
Feature profile     Remote Trigger
Reference           CompliancyTestTool-TestCaseDocument, Section 3.18.2, Table 177, Pages 150-151

Description         The Central System triggers a message from the Charge Point, but the Charge Point
                    rejects the message.

Purpose             To check whether the Central System is able to handle a reject on a triggered message.

Prerequisite(s)     The Central System supports the Remote Trigger feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
1.  The Central System sends a TriggerMessage.req with:
        - requestedMessage = MeterValues
2.  The Charge Point responds with a TriggerMessage.conf with:
        - status = Rejected

Tool validations
* Step 1:
    (Message: TriggerMessage.req)
    - requestedMessage should be MeterValues
* Step 2:
    (Message: TriggerMessage.conf)
    - status is Rejected

Expected result(s)
    The Central System processes the response from the Charge Point.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import TriggerMessageStatus

from charge_point import TziChargePoint16
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_055(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)

    # Set response to Rejected before starting
    cp._trigger_message_response_status = TriggerMessageStatus.rejected

    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send TriggerMessage.req, CP responds with Rejected
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'trigger-message', {'requestedMessage': 'MeterValues'}))
    await asyncio.wait_for(cp._received_trigger_message.wait(), timeout=ACTION_TIMEOUT)
    assert cp._trigger_message_requested == 'MeterValues'

    start_task.cancel()
