"""
Test case name      Send Local Authorization List - NotSupported
Test case Id        TC_043_1_CSMS
System under test   Central System
Document reference  Table 157, Section 3.14.2, Page 136/176

Description         The Charge Point can authorize an EV driver based on a local list that is set by
                    the Central System.

Purpose             To check whether a Central System can handle a NotSupported status, after sending
                    a Local Authorization List.

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    Charge Point (Tool)                         Central System (SUT)
    2. The Charge Point responds with a         1. The Central System sends a
       SendLocalList.conf                          SendLocalList.req

Tool validations
    Charge Point (Tool)                         Central System (SUT)
    * Step 2:                                   * Step 1:
      (Message: SendLocalList)                    (Message: SendLocalList.req)
      - Status is NotSupported                    - updateType should be Full

Expected result(s) / behaviour
    Charge Point (Tool)                         Central System (SUT)
    n/a                                         The Central System is able to send a local
                                                list and is able to receive a NotSupported
                                                response.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import UpdateStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_043_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # CP responds NotSupported for SendLocalList
    cp._send_local_list_response_status = UpdateStatus.not_supported
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send SendLocalList.req → CP responds NotSupported
    await asyncio.wait_for(cp._received_send_local_list.wait(), timeout=ACTION_TIMEOUT)
    assert cp._send_local_list_data['update_type'] == 'Full'

    start_task.cancel()
