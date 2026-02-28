"""
Test case name      Send Local Authorization List - Full
Test case Id        TC_043_4_CSMS
System under test   Central System
Reference           CompliancyTestTool-TestCaseDocument 2025-11, Section 3.14.2, Table 159,
                    p.136-137/176

Description         The Charge Point can authorize an EV driver based on a local list that is set by
                    the Central System.

Purpose             Check whether a Local Authorization List can be sent to a Charge Point to
                    authorize an EV driver.

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile and
                    has at least 1 IdToken to add to the local authorization list.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    Charge Point (Tool)                             Central System (SUT)
    2. The Charge Point responds with a              1. The Central System sends a SendLocalList.req
       SendLocalList.conf

Tool validations
    * Step 1: (Message: SendLocalList.req)
        - UpdateType should be Full.
        - All localAuthorizationList entries have an idTagInfo.
    * Step 2: (Message: SendLocalList.conf)
        - Status is Accepted.

Expected result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): The Central System is able to send a local list.
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
async def test_tc_043_4(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # CP responds Accepted for SendLocalList (Full)
    cp._send_local_list_response_status = UpdateStatus.accepted
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send SendLocalList.req → CP responds Accepted
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'send-local-list', {
        'listVersion': 1,
        'updateType': 'Full',
        'localAuthorizationList': [{'idTag': VALID_ID_TAG, 'idTagInfo': {'status': 'Accepted'}}],
    }))
    await asyncio.wait_for(cp._received_send_local_list.wait(), timeout=ACTION_TIMEOUT)
    # Validate updateType is Full
    assert cp._send_local_list_data['update_type'] == 'Full'

    # Validate all localAuthorizationList entries have an idTagInfo
    auth_list = cp._send_local_list_data.get('local_authorization_list') or []
    assert len(auth_list) > 0, "localAuthorizationList should not be empty"
    for entry in auth_list:
        assert 'id_tag_info' in entry, f"Entry missing idTagInfo: {entry}"

    start_task.cancel()
