"""
Test case name      Stop transaction options - EVDisconnected - Charging Station side
Test case Id        TC_E_14_CSMS
Use case Id(s)      E06(S2)
Requirement(s)      E06.FR.02

Requirement Details:
    E06.FR.02: The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType =
               Ended) to the CSMS.
        Precondition: TxStopPoint contains: EVConnected AND Connection between Charging Station and EV is
                      lost.
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the stop options.

Purpose             To verify if the CSMS is able to handle a Charging Station that stops a transaction when
                    the EV and EVSE are disconnected at the Charging Station side.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPostSession

Test Scenario
1. Execute Reusable State EVDisconnected

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
from reusable_states.ev_connected_post_session import ev_connected_post_session
from reusable_states.ev_disconnected import ev_disconnected
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_14(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EVConnectedPostSession
    await ev_connected_post_session(cp)

    # 1. Execute Reusable State EVDisconnected
    await ev_disconnected(cp)

    start_task.cancel()
