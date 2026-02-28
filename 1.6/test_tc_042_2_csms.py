"""
Test case name      Get Local List Version (empty)
Test case Id        TC_042_2_CSMS
System under test   Central System
Document reference  Section 3.14.1, Table 156, page 135/176

Description         The Central System can request a Charge Point for the version number of the
                    Local Authorization List.

Purpose             Check whether a Central System is able to retrieve the local list version from
                    a Charge Point.

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    Charge Point (Tool)                          Central System (SUT)
    2. The Charge Point responds with a          1. The Central System sends a
       GetLocalListVersion.conf.                    GetLocalListVersion.req.

Tool validations
    Charge Point (Tool):
        * Step 2: (Message: GetLocalListVersion.conf)
            - listVersion is 0
    Central System (SUT):
        * Step 1: n/a

Expected result(s) / behaviour
    n/a
"""

import asyncio
import os
import pytest

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
async def test_tc_042_2(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # Empty local list → respond with listVersion=0
    cp._local_list_version = 0
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send GetLocalListVersion.req → CP responds with listVersion=0
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'get-local-list-version', {}))
    await asyncio.wait_for(cp._received_get_local_list_version.wait(), timeout=ACTION_TIMEOUT)

    start_task.cancel()
