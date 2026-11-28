"""
Test case name      Change Availability EVSE - Operative to inoperative
Test case Id        TC_G_03_CSMS
Use case Id(s)      G03
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers how the CSMS requests the Charging Station to change the
                    availability of one of the EVSEs from Operative to Inoperative. An EVSE is considered
                    Operative in any status other than Faulted and Unavailable.

Purpose             To verify if the CSMS is able to perform the change availability mechanism as described at
                    the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State Unavailable for <Configured evseId>

Tool validations
N/a

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.unavailable import unavailable
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_g_03(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State Unavailable for <Configured evseId>
    await unavailable(cp, evse_id=CONFIGURED_EVSE_ID)

    start_task.cancel()
