"""
Test case name      Get Local List Version - No list available
Test case Id        TC_D_09_CSMS
Use case Id(s)      D02
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS can request a Charging Station for the version number of the Local Authorization
                    List by sending a GetLocalListVersionRequest.

Purpose             To verify if the CSMS is able to request the Local Authorization List version according to
                    the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to get a Local Authorization list version

1. The CSMS sends a GetLocalListVersionRequest
2. The Test System responds with a GetLocalListVersionResponse with versionNumber 0

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
async def test_tc_d_09(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to get a Local Authorization list version
    # 1. The CSMS sends a GetLocalListVersionRequest
    # 2. The Test System responds with a GetLocalListVersionResponse with versionNumber 0:
    #    no Local Authorization List is installed
    cp.local_list_version = 0
    await cp.wait_for_request(
        'GetLocalListVersion', manual_action=send_call(BASIC_AUTH_CP, 'GetLocalListVersion'))

    start_task.cancel()
