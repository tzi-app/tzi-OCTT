"""
Test case name      Local start transaction - Authorization first - Success
Test case Id        TC_E_04_CSMS
Use case Id(s)      E03
Requirement(s)      E03.FR.02

Requirement Details:
    E03.FR.02: The CSMS SHALL send a TransactionEventResponse that includes an authorization status.
        Precondition: E03.FR.01
System under test   CSMS

Description         OCPP 2.x.x allows an EV driver to either first connect the EV and EVSE OR present a form
                    of identification.
                    Both sequences will result in being able to charge.

Purpose             To verify if the CSMS is able to handle a Charging Station that is able to start a
                    charging session when the
                    EV driver first presents a form of identification, before connecting the EV and EVSE.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State Authorized
2. Execute Reusable State EnergyTransferStarted

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.authorized import authorized
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_04(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State Authorized
    await authorized(cp)

    # 2. Execute Reusable State EnergyTransferStarted
    await energy_transfer_started(cp)

    start_task.cancel()
