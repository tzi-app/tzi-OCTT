"""
Test case name      Stop transaction options - EnergyTransfer stopped - StopAuthorized
Test case Id        TC_E_08_CSMS
Use case Id(s)      E06(S6)
Requirement(s)      E06.FR.07

Requirement Details:
    E06.FR.07: The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType =
               Ended) to the CSMS.
        Precondition: TxStopPoint contains: EnergyTransfer AND Energy transfer stops
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the stop options.

Purpose             To verify if the CSMS is able to handle a Charging Station that stops a transaction when
                    the energy transfer stopped normally.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is StopAuthorized

Test Scenario
1. The Test System sends a TransactionEventRequest
    - With triggerReason is ChargingStateChanged
    - transactionInfo.chargingState is EVConnected
    - transactionInfo.stoppedReason is Local
    - eventType is Ended
2. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.stop_authorized import stop_authorized
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_08(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is StopAuthorized
    await stop_authorized(cp)

    # 1. The Test System sends a TransactionEventRequest
    #    - With triggerReason is ChargingStateChanged
    #    - transactionInfo.chargingState is EVConnected
    #    - transactionInfo.stoppedReason is Local
    #    - eventType is Ended
    # 2. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='ChargingStateChanged',
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': cp.session.transaction_id,
            'charging_state': 'EVConnected',
            'stopped_reason': 'Local',
        },
    ))

    start_task.cancel()
