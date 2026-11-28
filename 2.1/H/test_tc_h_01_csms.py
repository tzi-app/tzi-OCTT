"""
Test case name      Reserve a specific EVSE - Accepted - Valid idToken
Test case Id        TC_H_01_CSMS
Use case Id(s)      H01(S2), H03
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to reserve a specific EVSE for a specific IdToken by sending a
                    ReserveNowRequest containing an evseId.

Purpose             To verify if the CSMS is able to request the Charging Station to reserve a specific EVSE,
                    until the EV Driver with the specified IdToken arrives.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State Reserved for <Configured evseId>

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.reserved import reserved
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_h_01(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State Reserved for <Configured evseId>
    await reserved(cp, evse_id=CONFIGURED_EVSE_ID)

    start_task.cancel()
