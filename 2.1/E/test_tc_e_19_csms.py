"""
Test case name      Stop transaction options - ParkingBayUnoccupied
Test case Id        TC_E_19_CSMS
Use case Id(s)      E06(S1)
Requirement(s)      E06.FR.01

Requirement Details:
    E06.FR.01: The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType =
               Ended) to the CSMS.
        Precondition: TxStopPoint contains: ParkingBayOccupancy AND Parking Bay Detector no longer detects the
                      "EV"
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the stop options.

Purpose             To verify if the CSMS is able to handle a Charging Station that stops a transaction when
                    the EV left the parking bay.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVDisconnected

Test Scenario
1. The Test System sends a TransactionEventRequest With
    - triggerReason is EVDeparted
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
from reusable_states.ev_disconnected import ev_disconnected
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_19(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EVDisconnected
    # The station of this test case stops a transaction when the EV leaves the parking bay
    # (TxStopPoint ParkingBayOccupancy), so the transaction is still going on after the EV has
    # been disconnected: the TransactionEventRequest of that state has eventType Updated.
    await ev_disconnected(cp, ends_transaction=False)

    # 1. The Test System sends a TransactionEventRequest With
    #    - triggerReason is EVDeparted
    #    - transactionInfo.stoppedReason is Local
    #    - eventType is Ended
    # 2. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='EVDeparted',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': cp.session.transaction_id, 'stopped_reason': 'Local'},
    ))

    start_task.cancel()
