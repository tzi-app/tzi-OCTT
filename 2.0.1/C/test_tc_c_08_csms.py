"""
Test case name      Authorization through authorization cache - Accepted
Test case Id        TC_C_08_CSMS
Use case Id(s)      C12
Requirement(s)      C12.FR.03

Requirement Details:
    C12.FR.03: C12.FR.02 AND The CSMS SHALL check the authorization status of the IdToken when processing this TransactionEventRequest.
        Precondition: C12.FR.02
System under test   CSMS

Description         This test case describes how the EV Driver is authorized to start a transaction while the Charging Station
                    uses Cached IdToken. This enables the EV Driver to Online start a transaction by using the Authorization
                    Cache in which the Charging Station can respond faster, as no AuthorizeRequest is being sent.
                    Purpose To verify if the CSMS is able to respond correctly when an idToken which has status "Accepted" in the
                    charging stations cache is presented according to the mechanism as described in the OCPP specification.

Prerequisite(s) N/a
Before (Preparations)
    Configuration State: N/a
    Memory State: N/a
    Charging State: State is EVConnectedPreSession

Test scenario
Charging Station CSMS
1. The OCTT sends a TransactionEventRequest with
    - triggerReason Authorized
    - idToken <Valid id token configured in AuthorizationCache>
    - eventType Updated

    Note(s):
        - TxStartPoint contains ParkingBayOccupancy

2. The CSMS responds with a TransactionEventResponse
    - idTokenInfo.status Accepted
"""

import asyncio
import pytest
import os

from ocpp.v201.enums import (
    AuthorizationStatusEnumType as AuthorizationStatusType,
    TriggerReasonEnumType as TriggerReasonType,
    TransactionEventEnumType as TransactionEventType,
)
from ocpp.v201.call import TransactionEvent
from ocpp.v201.datatypes import IdTokenType
from tzi_charge_point import TziChargePoint
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from reusable_states.parking_bay_occupied import parking_bay_occupied
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, validate_schema

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_08(connection):
    token_id = os.environ['VALID_ID_TOKEN']  # Changed to a valid ID token
    token_type = os.environ['VALID_ID_TOKEN_TYPE']  # Changed to a valid ID token type
    evse_id = 1
    connector_id = 1

    assert connection.open
    cp = TziChargePoint(BASIC_AUTH_CP, connection)

    start_task = asyncio.create_task(cp.start())
    await parking_bay_occupied(cp, evse_id=evse_id)
    await ev_connected_pre_session(cp, evse_id=evse_id, connector_id=connector_id)

    transaction_id = generate_transaction_id()

    id_token = IdTokenType(id_token=token_id, type=token_type)

    event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.authorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            "transaction_id": transaction_id,
            "charging_state": "EVConnected",
        },
        id_token=id_token,
        evse={
            "id": evse_id,
            "connector_id": connector_id
        }
    )
    response = await cp.send_transaction_event_request(event)

    assert response is not None
    assert validate_schema(data=response, schema_file_name='../schema/TransactionEventResponse.json')

    assert response.id_token_info is not None
    assert response.id_token_info.status == AuthorizationStatusType.accepted

    start_task.cancel()
