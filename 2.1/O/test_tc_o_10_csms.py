"""
Test case name      Set Display Message - Specific transaction - UnknownTransaction
Test case Id        TC_O_10_CSMS
Use case Id(s)      O02
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSMS can attempt to set a DisplayMessage for a
                    transactionId that the CS does not know. The CS will respond with a
                    SetDisplayMessageResponse status of UnknownTransaction.

Purpose             To verify if the CSMS is able to send a display message correctly according the mechanism
                    as described in the OCPP specification for a specific transaction.

Prerequisite(s)     If the CSMS supports sending a SetDisplayMessageRequest with a transactionId for a
                    transaction that does not exist.

Configuration State N/a

Memory State        N/a

Reusable State      State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to send a display message for a specific transaction.

1. The CSMS sends a SetDisplayMessageRequest
2. The Test System responds with a SetDisplayMessageResponse with
    status UnknownTransaction

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.transactionId not omit AND
    - message.priority <Configured Priority>

Post scenario validations:
    - N/a
"""

import asyncio
import os
import uuid

import pytest

from charge_point import TziChargePoint21
from display_messages import display_message, request_display_message, validate_message
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_o_10(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: If the CSMS supports sending a SetDisplayMessageRequest with a transactionId
    # for a transaction that the Charging Station does not know.
    # Reusable State: State is EnergyTransferStarted
    await energy_transfer_started(cp)

    # Manual Action: Request the CSMS to send a display message for a specific transaction.
    # 1. The CSMS sends a SetDisplayMessageRequest
    # 2. The Test System responds with a SetDisplayMessageResponse with status UnknownTransaction
    request = await request_display_message(
        cp, display_message(transactionId=str(uuid.uuid4())), status='UnknownTransaction')
    # message.transactionId not omit AND message.priority <Configured Priority>
    assert request.message.transaction_id is not None, \
        "SetDisplayMessageRequest.message.transactionId must not be omitted"
    validate_message(request)

    start_task.cancel()
