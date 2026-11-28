"""
Test case name      Start transaction options - ParkingBayOccupied
Test case Id        TC_E_12_CSMS
Use case Id(s)      E01(S1)
Requirement(s)      E01.FR.01

Requirement Details:
    E01.FR.01: The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType =
               Started) to the CSMS.
        Precondition: TxStartPoint contains: ParkingBayOccupancy AND Parking Bay Detector detects an "EV" AND
                      No transaction has started yet
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the start options.

Purpose             To verify if the CSMS is able to handle a Charging Station that starts a transaction when
                    the EV and EVSE are connected.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a TransactionEventRequest With
    - eventType is Started
    - triggerReason is EVDetected
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
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_12(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The Test System sends a TransactionEventRequest With
    #    - eventType is Started
    #    - triggerReason is EVDetected
    # 2. The CSMS responds with a TransactionEventResponse
    transaction_id = cp.session.start_transaction()
    await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='EVDetected',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
    ))

    start_task.cancel()
