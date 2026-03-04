"""
TC_E_21 - Stop transaction options - StopAuthorized - Remote
Use case: E06(S3), F03 | Requirements: E06.FR.03, F03.FR.01, F03.FR.09, F03.FR.10
E06.FR.03: TxStopPoint contains: Authorized AND EV Driver is authorized to stop a transaction. The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS.
    Precondition: TxStopPoint contains: Authorized AND EV Driver is authorized to stop a transaction.
F03.FR.01: When the CSMS receives a remote stop transaction trigger (For example when terminating using a smartphone app, exceeding a (non local) prepaid credit.) The CSMS SHALL send a RequestStopTransactionRequest to the Charging Station with the transactionId of the transaction.
    Precondition: When the CSMS receives a remote stop transaction trigger (For example when terminating using a smartphone app, exceeding a (non local) prepaid credit.)
F03.FR.09: When sending a TransactionEventRequest The Charging Station SHALL set the triggerReason to inform the CSMS about what triggered the event. What reason to use is described in the description of TriggerReasonEnumType.
    Precondition: When sending a TransactionEventRequest
F03.FR.10: The Charging Station SHALL unlock the connector when receiving RequestStopTransactionRequest.
System under test: CSMS

Purpose: Verify the CSMS handles a Charging Station that stops a transaction after receiving a
RequestStopTransactionRequest from the CSMS.

Before: Reusable State EnergyTransferStarted

Manual Action: Trigger the CSMS UI/API to send a RequestStopTransaction for the ongoing transaction.

Test validates:
  - CSMS sends RequestStopTransactionRequest with the correct transactionId
  - CS responds Accepted
  - CS sends TransactionEvent Ended with triggerReason=RemoteStop, stoppedReason=Remote
  - CSMS responds to TransactionEvent

Configuration:
    CSMS_ADDRESS     - WebSocket URL of the CSMS
    BASIC_AUTH_CP    - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD - Charge Point password
    VALID_ID_TOKEN   - Valid idToken value
    VALID_ID_TOKEN_TYPE - Valid idToken type
    CONFIGURED_EVSE_ID   - EVSE id (default 1)
    CONFIGURED_CONNECTOR_ID - Connector id (default 1)
    CSMS_ACTION_TIMEOUT - Seconds to wait for CSMS to send RequestStopTransaction (default 30)
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.call import TransactionEvent
from ocpp.v201.enums import (
    TransactionEventEnumType as TransactionEventType,
    TriggerReasonEnumType as TriggerReasonType,
    ReasonEnumType as StoppedReasonType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, generate_transaction_id, now_iso
from trigger import send_call
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [
    (BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))
], indirect=True)
async def test_tc_e_21(connection):
    """Stop transaction options - StopAuthorized - Remote (E06.FR.03, F03.FR.01).
    E06.FR.03: TxStopPoint contains: Authorized AND EV Driver is authorized to stop a transaction. The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType = Ended) to the CSMS.
        Precondition: TxStopPoint contains: Authorized AND EV Driver is authorized to stop a transaction.
    F03.FR.01: When the CSMS receives a remote stop transaction trigger (For example when terminating using a smartphone app, exceeding a (non local) prepaid credit.) The CSMS SHALL send a RequestStopTransactionRequest to the Charging Station with the transactionId of the transaction.
        Precondition: When the CSMS receives a remote stop transaction trigger (For example when terminating using a smartphone app, exceeding a (non local) prepaid credit.)
    """
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    # Before: EnergyTransferStarted
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Step 1-2: Trigger CSMS to send RequestStopTransactionRequest
    async def trigger_remote_stop():
        await asyncio.sleep(1)
        await send_call(BASIC_AUTH_CP, "RequestStopTransaction",
                        {"transactionId": transaction_id})

    trigger_task = asyncio.create_task(trigger_remote_stop())

    await asyncio.wait_for(
        cp._received_request_stop_transaction.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    # Validate the transactionId matches
    assert cp._request_stop_transaction_data is not None
    assert cp._request_stop_transaction_data['transaction_id'] == transaction_id

    # Step 3-4: CS sends TransactionEvent Ended / RemoteStop / Remote
    end_event = TransactionEvent(
        event_type=TransactionEventType.ended,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.remote_stop,
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'stopped_reason': StoppedReasonType.remote,
        },
    )
    end_response = await cp.send_transaction_event_request(end_event)
    assert end_response is not None

    start_task.cancel()
