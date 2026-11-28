"""
Test case name      Clear Authorization Data in Authorization Cache - Accepted
Test case Id        TC_C_37_CSMS
Use case Id(s)      C11
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers how the Charging Station autonomously stores a record of previously
                    presented identifiers that have been successfully authorized by the CSMS in the
                    Authorization Cache. (Successfully meaning: a response received on a message containing an
                    IdToken)

Purpose             To verify if the CSMS is able to request the Charging Station to clear all identifiers
                    from the Authorization Cache according to the mechanism as described in the OCPP
                    specification.

Prerequisite(s)     - N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a ClearCacheRequest
2. The Test System responds with a ClearCacheResponse with status Accepted

Tool validations
- N/a

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_37(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a ClearCacheRequest
    # 2. The Test System responds with a ClearCacheResponse with status Accepted
    cp.set_response('ClearCache', status='Accepted')
    await cp.wait_for_request('ClearCache', manual_action=send_call(BASIC_AUTH_CP, 'ClearCache'))

    start_task.cancel()
