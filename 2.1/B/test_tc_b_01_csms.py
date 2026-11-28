"""
Test case name      Cold Boot Charging Station - Accepted
Test case Id        TC_B_01_CSMS
Use case Id(s)      B01
Requirement(s)      B01.FR.02

Requirement Details:
    B01.FR.02: The CSMS SHALL respond to indicate whether it will accept the Charging Station.
        Precondition: B01.FR.01 The CSMS has received BootNotificationRequest from the Charging Station.
System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about
                    the Charging Station to the CSMS on startup AND it allows the Charging Station to request
                    whether it is allowed to start sending other OCPP messages.

Purpose             To verify whether the CSMS is able to accept the communications of a registered Charging
                    Station.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State Booted

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
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_01(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # 1. Execute Reusable State Booted
    await booted(cp)

    start_task.cancel()
