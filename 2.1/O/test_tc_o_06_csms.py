"""
Test case name      Set Display Message - Specific transaction - Success
Test case Id        TC_O_06_CSMS
Use case Id(s)      O02
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can set a message to be displayed on a Charging Station
                    for a specific transaction. Depending on the given parameters the message shall be
                    displayed a certain way on the Charging Station.

Purpose             To verify if the CSMS is able to send a display message correctly according the mechanism
                    as described in the OCPP specification for a specific transaction.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to send a display message for a specific transaction.

1. The CSMS sends a SetDisplayMessageRequest
2. The Test System responds with a SetDisplayMessageResponse with status Accepted
3. Execute Reusable State EVDisconnected

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.transactionId Same ID as previously returned by the Charging Station AND
    - message.priority <Configured Priority>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from display_messages import display_message, request_display_message, validate_message
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_disconnected import ev_disconnected
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_o_06(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # Manual Action: Request the CSMS to send a display message for a specific transaction.
    # 1. The CSMS sends a SetDisplayMessageRequest
    # 2. The Test System responds with a SetDisplayMessageResponse with status Accepted
    request = await request_display_message(cp, display_message(transactionId=transaction_id))
    # message.transactionId Same ID as previously returned by the Charging Station AND
    # message.priority <Configured Priority>
    assert request.message.transaction_id == transaction_id, \
        f"Expected SetDisplayMessageRequest.message.transactionId {transaction_id}, " \
        f"got {request.message.transaction_id}"
    validate_message(request)

    # 3. Execute Reusable State EVDisconnected
    await ev_disconnected(cp)

    start_task.cancel()
