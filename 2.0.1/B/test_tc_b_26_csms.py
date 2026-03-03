"""
Test case name      Reset EVSE - With Ongoing Transaction - OnIdle
Test case Id        TC_B_26_CSMS
Use case Id(s)      B12
Requirement(s)      B12.FR.07

Requirement Details:
    B12.FR.07: If an evseId is supplied AND If a transaction is in progress on the EVSE and an OnIdle reset is received. The transaction on the EVSE SHALL be terminated normally, before the reset, e.g. as in E06 - Stop Transaction.
        Precondition: If an evseId is supplied AND If a transaction is in progress on the EVSE and an OnIdle reset is received.
System under test   CSMS

Description         This test case covers how the CSMS can remotely request the Charging Station to reset an EVSE
                    by sending a ResetRequest during a transaction. When ResetRequest "OnIdle" is sent the charging
                    stations schedules a reboot after all transactions are stopped.
Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP specification.

Prerequisite(s)     n/a

Before (Reusable State): EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to reboot the charging EVSE with status OnIdle
1. The CSMS sends a ResetRequest with status OnIdle and evseID <Configured evseId>
2. The OCTT responds with a ResetResponse with status Scheduled
3. The OCTT sends a TransactionEventRequest (Updated, StopAuthorized)
4. The CSMS responds with a TransactionEventResponse
5. The OCTT sends a TransactionEventRequest (Ended, EVCommunicationLost)
6. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message: ResetRequest
    - type OnIdle
    - evseId <Configured evseId>

Post scenario validations:
    - N/a
"""

import asyncio
import pytest
import os
import logging
from ocpp.v201.enums import (
    RegistrationStatusEnumType, ConnectorStatusEnumType, ResetStatusEnumType
)
from ocpp.v201.call import TransactionEvent

from tzi_charge_point import TziChargePoint
from trigger import reset
from utils import get_basic_auth_headers, generate_transaction_id, now_iso

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_26(connection):
    """Reset EVSE - With Ongoing Transaction - OnIdle: scheduled EVSE reset after transaction."""
    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    cp._reset_response_status = ResetStatusEnumType.scheduled
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Simulate EnergyTransferStarted - start a transaction
    transaction_id = generate_transaction_id()

    started_event = TransactionEvent(
        event_type='Started',
        timestamp=now_iso(),
        trigger_reason='CablePluggedIn',
        seq_no=0,
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': 'EVConnected',
        },
        evse={'id': CONFIGURED_EVSE_ID, 'connector_id': CONFIGURED_CONNECTOR_ID},
        id_token={'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
    )
    await cp.send_transaction_event_request(started_event)

    # Step 1-2: Trigger CSMS to send ResetRequest with type OnIdle for specific EVSE
    trigger_task = asyncio.create_task(
        reset(BASIC_AUTH_CP, "OnIdle", evse_id=CONFIGURED_EVSE_ID)
    )

    await asyncio.wait_for(
        cp._received_reset.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task

    assert cp._reset_data is not None
    assert cp._reset_data['type'] == 'OnIdle', \
        f"Expected OnIdle reset type, got: {cp._reset_data['type']}"
    assert cp._reset_data['evse_id'] == CONFIGURED_EVSE_ID, \
        f"Expected evseId {CONFIGURED_EVSE_ID}, got: {cp._reset_data['evse_id']}"

    # Step 3-4: Send TransactionEventRequest (Updated, StopAuthorized)
    updated_event = TransactionEvent(
        event_type='Updated',
        timestamp=now_iso(),
        trigger_reason='StopAuthorized',
        seq_no=1,
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': 'EVConnected',
        },
        id_token={'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
    )
    await cp.send_transaction_event_request(updated_event)

    # Step 5-6: Send TransactionEventRequest (Ended, EVCommunicationLost)
    ended_event = TransactionEvent(
        event_type='Ended',
        timestamp=now_iso(),
        trigger_reason='EVCommunicationLost',
        seq_no=2,
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': 'Idle',
            'stopped_reason': 'EVDisconnected',
        },
    )
    await cp.send_transaction_event_request(ended_event)

    start_task.cancel()
