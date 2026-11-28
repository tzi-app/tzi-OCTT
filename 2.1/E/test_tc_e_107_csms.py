"""
Test case name      Transactions with fixed cost, energy or time - CS specifies time limit
Test case Id        TC_E_107_CSMS
Use case Id(s)      E16
Requirement(s)      …
System under test   CSMS

Description         EV Driver or CSMS specifies a limit in cost, energy, state of charge or time for
                    transaction.

Purpose             To verify whether the CSMS correctly handles transactions where the Charging Station
                    specifies a time limit.

Prerequisite(s)     Test System has TxCtlr.SupportedLimits contains maxTime.

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason LimitSet
    - transactionInfo.transactionLimit.maxTime 120
2. The CSMS responds with a TransactionEventResponse

Note: The test system waits for the maxTime transactionLimit to be reached.

3. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - triggerReason TimeLimitReached
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message TransactionEventResponse with:
    - transactionLimit is <omitted>

Post scenario validations:
    N/a
"""

import asyncio
import os
import time

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

# transactionInfo.transactionLimit.maxTime of the scenario, in seconds
MAX_TIME = 120


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_107(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisite: Test System has TxCtrlr.SupportedLimits contains maxTime.
    cp.variables = {'TxCtrlr.SupportedLimits': 'maxTime'}
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    # The timer of a time limit is relative to the start of the transaction (E16.FR.09).
    transaction_started = time.monotonic()
    transaction_id = await energy_transfer_started(cp)

    # 1. The Test System sends a TransactionEventRequest with
    #    - eventType Updated
    #    - triggerReason LimitSet
    #    - transactionInfo.transactionLimit.maxTime 120
    # 2. The CSMS responds with a TransactionEventResponse
    response = await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='LimitSet',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'transaction_limit': {'max_time': MAX_TIME}},
    ))
    assert response.transaction_limit is None, \
        f"TransactionEventResponse.transactionLimit must be omitted, got {response.transaction_limit}"

    # Note: The test system waits for the maxTime transactionLimit to be reached.
    await asyncio.sleep(max(0.0, MAX_TIME - (time.monotonic() - transaction_started)))

    # 3. The Test System sends a TransactionEventRequest with
    #    - eventType Ended
    #    - triggerReason TimeLimitReached
    # 4. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='TimeLimitReached',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
    ))

    start_task.cancel()
