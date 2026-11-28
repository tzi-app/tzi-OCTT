"""
Test case name      Reset Sequence Number - CSMS accepting seqNo = 0 at start of transaction
Test case Id        TC_E_53_CSMS
Use case Id(s)      E01
Requirement(s)      E01.FR.07

Requirement Details:
    E01.FR.07: The Charging Station SHALL set the message’s seqNo field as specified in Sequence Number
               Generation.
        Precondition: When a TransactionEventRequest has to be created
System under test   CSMS

Description         OCPP 2.0.1 Edition 2 recommends that seqNo starts at 0 for every transaction. CSMS must
                    therefore be robust to a seqNo that is not continuously increasing, but that restarts for
                    new transactions. Since a TransactionEventRequest cannot be rejected, this can only be
                    detected by either the complete absence of a TranactionEventResponse from CSMS or an
                    otherwise misbehaving CSMS.

Purpose             To verify if the CSMS accepts that a new transactions starts with a seqNo = 0.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State EnergyTransferStarted
    Note(s): New transaction will use seqNo 0 for the first TransactionEventRequest.
2. Execute Reusable State EVDisconnected
3. Execute Reusable State EnergyTransferStarted
    Note(s): New transaction will use seqNo 0 for the first TransactionEventRequest.
4. Execute Reusable State EVDisconnected

Tool validations
* Step 1:
    CSMS accepts the message TransactionEventRequest with eventType = Started and seqNo = 0 and answers with a
    TransactionEventResponse message.
* Step 3:
    CSMS accepts the message TransactionEventRequest with eventType = Started and seqNo = 0 and answers with a
    TransactionEventResponse message.

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_disconnected import ev_disconnected
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


def started_events(cp):
    """The TransactionEventRequests with eventType Started that the station has sent."""
    return [payload for action, payload in cp.sent_requests
            if action == 'TransactionEvent' and payload['eventType'] == 'Started']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_53(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State EnergyTransferStarted
    #    Note(s): New transaction will use seqNo 0 for the first TransactionEventRequest.
    first_transaction_id = await energy_transfer_started(cp)
    # The CSMS accepted the TransactionEventRequest with eventType = Started and seqNo = 0, and
    # answered it with a TransactionEventResponse: otherwise the state had failed.
    assert [event['seqNo'] for event in started_events(cp)] == [0]

    # 2. Execute Reusable State EVDisconnected
    await ev_disconnected(cp)

    # 3. Execute Reusable State EnergyTransferStarted
    #    Note(s): New transaction will use seqNo 0 for the first TransactionEventRequest.
    second_transaction_id = await energy_transfer_started(cp)
    assert second_transaction_id != first_transaction_id
    assert [event['seqNo'] for event in started_events(cp)] == [0, 0]

    # 4. Execute Reusable State EVDisconnected
    await ev_disconnected(cp)

    start_task.cancel()
