"""
Test case name      Send Local Authorization List - Failed
Test case Id        TC_043_3_CSMS
System under test   Central System (SUT)
Reference           CompliancyTestTool-TestCaseDocument, Section 3.14.2, Table 158, Page 136

Description         The Charge Point can authorize an EV driver based on a local list that is set by
                    the Central System.

Purpose             To check whether a Central System can handle a Rejected status, after sending a
                    Local Authorization List.
                    NOTE: The official doc says "Rejected" in Purpose but "Failed" in Tool
                    validations and Expected results. Likely a doc typo - should be "Failed".

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
1. The Central System sends a SendLocalList.req.
2. The Charge Point responds with a SendLocalList.conf.

Tool validations
    * Step 1: (Message: SendLocalList.req)
        - updateType should be Full.
    * Step 2: (Message: SendLocalList)
        - Status is Failed.

Expected result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): The Central System is able to send a local list and is able to receive a
    Failed response.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import UpdateStatus

from charge_point import TziChargePoint16
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
VALID_ID_TAG = os.environ.get('VALID_ID_TOKEN', 'TEST_TAG')


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_043_3(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # CP responds Failed for SendLocalList
    cp._send_local_list_response_status = UpdateStatus.failed
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send SendLocalList.req → CP responds Failed
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'send-local-list', {
        'listVersion': 1,
        'updateType': 'Full',
        'localAuthorizationList': [{'idTag': VALID_ID_TAG, 'idTagInfo': {'status': 'Accepted'}}],
    }))
    await asyncio.wait_for(cp._received_send_local_list.wait(), timeout=ACTION_TIMEOUT)
    assert cp._send_local_list_data['update_type'] == 'Full'

    start_task.cancel()
