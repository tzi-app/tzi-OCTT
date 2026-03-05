"""
Test case name      Authorization by GroupId - Success
Test case Id        TC_C_39_CSMS
Use case Id(s)      C09
Requirement(s)      C09.FR.02, C09.FR.03

Requirement Details:
    C09.FR.02: IdTokens that are part of the same group for authorization purposes SHALL have a common group identifier in the optional groupIdToken element in IdTokenInfo.
    C09.FR.03: When a transaction has been authorized/started with a certain IdToken. An EV Driver with a different, valid IdToken, but with the same groupIdToken SHALL be authorized to stop the transaction.
        Precondition: When a transaction has been authorized/started with a certain IdToken.
System under test   CSMS

Description         This test case covers how a Charging Station can authorize an action for an EV Driver based on GroupId
                    information. This could for example be used if 2 people regularly use the same EV: they can use their own
                    IdToken (e.g. RFID card), and can deauthorize transactions that were started with the other idToken (with
                    the same GroupId).
                    Purpose To verify if the CSMS is able to correctly handle the Authorization of idTokens with the same GroupId
                    according to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a
Before (Preparations)
    Configuration State:    N/a
    Memory State:           Two valid idTokens with the same GroupId are configured

Reusable State(s):
    state is EVConnectedPreSession

Test Scenario
    1. The OCTT sends an AuthorizeRequest with idToken.idToken <Configured valid_idtoken2_idtoken>
        idToken.type <Configured valid_idtoken2_type>
    2. The CSMS responds with an AuthorizeResponse
    3. The OCTT sends a TransactionEventRequest with
        - triggerReason Authorized
        - idToken.idToken <Configured valid_idtoken_idtoken>
        - idToken.type <Configured valid_idtoken_type>
            if transaction was already started
                - eventType Updated
            else
                - eventType Started

    4. The CSMS responds with a TransactionEventResponse
    5. Execute Reusable State EnergyTransferStarted
    6. The OCTT sends an AuthorizeRequest with idToken.idToken <Configured valid_idtoken2_idtoken> idToken.type <Configured valid_idtoken2_type>
    7. The CSMS responds with an AuthorizeResponse
    8. The OCTT sends a TransactionEventRequest with
        - triggerReason StopAuthorized
        - idToken.idToken <Configured valid_idtoken2_idtoken>
        - idToken.type <Configured valid_idtoken2_type>
        - eventType Updated
    9. The CSMS responds with a TransactionEventResponse
    10. Execute Reusable State EVConnectedPostSession
    11. Execute Reusable State EVDisconnected

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
* Step 4:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
* Step 7:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
* Step 9:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
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
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_connected_post_session import ev_connected_post_session
from reusable_states.ev_disconnected import ev_disconnected
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, validate_schema

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_39(connection):
    token_id_1 = os.environ['VALID_ID_TOKEN']
    token_type_1 = os.environ['VALID_ID_TOKEN_TYPE']
    token_id_2 = os.environ['VALID_ID_TOKEN_2']
    token_type_2 = os.environ['VALID_ID_TOKEN_TYPE_2']
    group_id = os.environ['GROUP_ID']
    evse_id = 1
    connector_id = 1

    assert connection.open
    cp = TziChargePoint(BASIC_AUTH_CP, connection)

    start_task = asyncio.create_task(cp.start())

    # 1. The OCTT sends an AuthorizeRequest with idToken.idToken <Configured valid_idtoken2_idtoken>
    # idToken.type <Configured valid_idtoken2_type>
    authorization_response_1 = await cp.send_authorization_request(id_token=token_id_2, token_type=token_type_2)

    # 2. The CSMS responds with an AuthorizeResponse
    assert authorization_response_1 is not None
    assert validate_schema(data=authorization_response_1, schema_file_name='../schema/AuthorizeResponse.json')
    assert authorization_response_1.id_token_info['status'] == AuthorizationStatusType.accepted
    assert authorization_response_1.id_token_info['group_id_token']['id_token'] == group_id

    await ev_connected_pre_session(cp, evse_id=evse_id, connector_id=connector_id)

    # 3. The OCTT sends a TransactionEventRequest with
    # - triggerReason Authorized
    # - idToken.idToken <Configured valid_idtoken_idtoken>
    # - idToken.type <Configured valid_idtoken_type>
    transaction_id = generate_transaction_id()
    id_token = IdTokenType(id_token=token_id_1, type=token_type_1)

    event = TransactionEvent(
        event_type=TransactionEventType.started,
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
    transaction_event_response_1 = await cp.send_transaction_event_request(event)

    # 4. The CSMS responds with a TransactionEventResponse
    assert transaction_event_response_1 is not None
    assert validate_schema(data=transaction_event_response_1,
                           schema_file_name='../schema/TransactionEventResponse.json')
    assert transaction_event_response_1.id_token_info.status == AuthorizationStatusType.accepted
    assert transaction_event_response_1.id_token_info.group_id_token.id_token == group_id

    # 5. Execute Reusable State EnergyTransferStarted for the active transaction
    await energy_transfer_started(cp, evse_id=evse_id, connector_id=connector_id, transaction_id=transaction_id)

    # 6. The OCTT sends an AuthorizeRequest with idToken.idToken <Configured valid_idtoken2_idtoken> idToken.type <Configured valid_idtoken2_type>
    authorization_response_2 = await cp.send_authorization_request(id_token=token_id_2, token_type=token_type_2)

    # 7. The CSMS responds with an AuthorizeResponse
    assert authorization_response_2 is not None
    assert validate_schema(data=authorization_response_2, schema_file_name='../schema/AuthorizeResponse.json')
    assert authorization_response_2.id_token_info['status'] == AuthorizationStatusType.accepted
    assert authorization_response_2.id_token_info['group_id_token']['id_token'] == group_id

    # 8. The OCTT sends a TransactionEventRequest with
    # - triggerReason StopAuthorized
    # - idToken.idToken <Configured valid_idtoken2_idtoken>
    # - idToken.type <Configured valid_idtoken2_type>
    # - eventType Updated
    event = TransactionEvent(
        event_type=TransactionEventType.updated,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.stop_authorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            "transaction_id": transaction_id,
            "charging_state": "Charging",
        },
        id_token=IdTokenType(id_token=token_id_2, type=token_type_2),
        evse={
            "id": evse_id,
            "connector_id": connector_id
        }
    )
    transaction_event_response_2 = await cp.send_transaction_event_request(event)

    # 9. The CSMS responds with a TransactionEventResponse
    assert transaction_event_response_2 is not None
    assert validate_schema(data=transaction_event_response_2,
                           schema_file_name='../schema/TransactionEventResponse.json')
    assert transaction_event_response_2.id_token_info.status == AuthorizationStatusType.accepted
    assert transaction_event_response_2.id_token_info.group_id_token.id_token == group_id

    # 10. Execute Reusable State EVConnectedPostSession
    await ev_connected_post_session(cp, evse_id=evse_id, connector_id=connector_id, transaction_id=transaction_id)

    # 11. Execute Reusable State EVDisconnected
    await ev_disconnected(cp, evse_id=evse_id, connector_id=connector_id, transaction_id=transaction_id)
    start_task.cancel()
