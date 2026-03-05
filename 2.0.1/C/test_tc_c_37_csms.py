"""
Test case name      Clear Authorization Data in Authorization Cache - Accepted
Test case Id        TC_C_37_CSMS
Use case Id(s)      C11
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers how the Charging Station autonomously stores a record of previously presented
                    identifiers that have been successfully authorized by the CSMS in the Authorization Cache. (Successfully
                    meaning: a response received on a message containing an IdToken)
                    Purpose To verify if the CSMS is able to request the Charging Station to clear all identifiers from the Authorization
                    Cache according to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Before (Preparations)
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Test scenario
1. The CSMS sends a ClearCacheRequest
2. The OCTT responds with a ClearCacheResponse with status Accepted

Configuration
    The CSMS must be triggered externally (e.g., via CSMS admin API or UI) to send ClearCacheRequest
    to the connected Charging Station within CSMS_ACTION_TIMEOUT seconds.
    The MockChargePoint is pre-configured to respond with Accepted status (default).
"""

import asyncio
import pytest
import os

from tzi_charge_point import TziChargePoint
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_37(connection):
    assert connection.open
    cp = TziChargePoint(BASIC_AUTH_CP, connection)

    # Default _clear_cache_response_status is ClearCacheStatusType.accepted
    start_task = asyncio.create_task(cp.start())

    # Trigger CSMS to send ClearCacheRequest
    trigger_task = asyncio.create_task(send_call(BASIC_AUTH_CP, "ClearCache", {}))

    await asyncio.wait_for(cp._received_clear_cache.wait(), timeout=CSMS_ACTION_TIMEOUT)
    await trigger_task

    assert cp._received_clear_cache.is_set(), "CSMS did not send ClearCacheRequest within timeout"

    start_task.cancel()
