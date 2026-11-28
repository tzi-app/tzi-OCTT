"""
Test case name      Stop transaction options - Deauthorized - EV side disconnect
Test case Id        TC_E_17_CSMS
Use case Id(s)      E06(S3)
Requirement(s)      E06.FR.04

Requirement Details:
    E06.FR.04: See use case E05 - Start Transaction - Id not Accepted,
        Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a
                      TransactionEventResponse
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the start options.

Purpose             To verify if the CSMS is able to handle a Charging Station that stops a transaction when
                    the transaction gets deauthorized by a connection loss from the EV side and it has been
                    configured to do so.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferSuspended

Test Scenario
1. The Test System sends a TransactionEventRequest
    - triggerReason must be EVCommunicationLost
    - transactionInfo.chargingState must be Idle
    - transactionInfo.stoppedReason must be EVDisconnected
    - eventType must be Ended
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
from reusable_states.energy_transfer_suspended import energy_transfer_suspended
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_17(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferSuspended
    await energy_transfer_suspended(cp)

    # 1. The Test System sends a TransactionEventRequest
    #    - triggerReason must be EVCommunicationLost
    #    - transactionInfo.chargingState must be Idle
    #    - transactionInfo.stoppedReason must be EVDisconnected
    #    - eventType must be Ended
    # 2. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='EVCommunicationLost',
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': cp.session.transaction_id,
            'charging_state': 'Idle',
            'stopped_reason': 'EVDisconnected',
        },
    ))

    start_task.cancel()
