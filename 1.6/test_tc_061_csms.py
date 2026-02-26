"""
Test case name      Clear Authorization Data in Authorization Cache
Test case Id        TC_061_CSMS
OCPP version        1.6J
Chapter             3.3.2 Clear Authorization Data in Authorization Cache
Document ref        CompliancyTestTool-TestCaseDocument, Table 128, pages 113-114/176

System under test   Central System

Description         The Central System can clear the Authorization Cache of a Charge Point.

Purpose             Check whether the Central System can clear the Authorization Cache of a Charge Point.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. [CS -> CP] The Central System sends a ClearCache.req.
    2. [CP -> CS] The Charge Point responds with a ClearCache.conf.

Tool validation(s)
    * Step 2:
        (Message: ClearCache.conf)
        - status is Accepted

Expected result(s)
    - [CP] The Charge Point Authorization Cache is cleared.
    - [CS] The Central System is able to send a message to clear the cache.

Post scenario validations:
    n/a
"""

import asyncio
import os
import pytest

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_061(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ClearCache.req, CP responds Accepted (default)
    await asyncio.wait_for(cp._received_clear_cache.wait(), timeout=ACTION_TIMEOUT)
    assert cp._received_clear_cache.is_set()

    start_task.cancel()
