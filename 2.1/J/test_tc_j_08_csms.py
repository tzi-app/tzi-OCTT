"""
Test case name      Sampled Meter Values - Context Transaction.Begin - EVSE not known
Test case Id        TC_J_08_CSMS
Use case Id(s)      J02
Requirement(s)      J02.FR.19

Requirement Details:
    J02.FR.19: CSMS SHALL respond with TransactionEventResponse.
        Precondition: When CSMS receives a TransactionEventRequest
        Note: Failing to respond with TransactionEventResponse might cause the Charging Station to try the
              same message again.
System under test   CSMS

Description         The Charging Station samples the electrical meter or other sensor/transducer hardware to
                    provide information about its Meter Values. Depending on configuration settings, the
                    Charging Station will send Meter Values.

Purpose             To verify if the CSMS is able to handle a Charging Station sending start sampled Meter
                    Values, when a transaction starts.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State Authorized
2. Execute Reusable State EVConnectedPreSession
    - The TransactionEventRequest contains the MeterValue field.
    - sampledValue.context is Transaction.Begin
3. Execute Reusable State EnergyTransferStarted

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from metering import EnergyMeter
from reusable_states.authorized import authorized
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_j_08(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State Authorized
    await authorized(cp)

    # 2. Execute Reusable State EVConnectedPreSession
    #    - The TransactionEventRequest contains the MeterValue field.
    #    - sampledValue.context is Transaction.Begin
    await ev_connected_pre_session(cp, meter_value=[EnergyMeter().meter_value('Transaction.Begin')])

    # 3. Execute Reusable State EnergyTransferStarted
    await energy_transfer_started(cp)

    start_task.cancel()
