"""
Test case name      Authorization by GroupId - Invalid status with Local Authorization List
Test case Id        TC_C_43_CSMS
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
                    Purpose To verify if the CSMS is able to correctly handle the Authorization of idTokens with the same
                    GroupId which are located in the Local Authorization List according to the mechanism as described in the
                    OCPP specification.

Prerequisite(s)     N/a

Before (Preparations)
    Configuration State:    N/a
    Memory State:           Two known valid idTokens with same GroupId are configured
    Reusable State(s):      State is EVConnectedPreSession

Test Scenario
1. The OCTT sends a TransactionEventRequest with
    - triggerReason Authorized
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
    - eventType Started (or Updated if transaction already started)

2. The CSMS responds with a TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>

3. Execute Reusable State EnergyTransferStarted

4. The OCTT sends an AuthorizeRequest with
    - idToken.idToken <Configured valid_idtoken2_idtoken>
    - idToken.type <Configured valid_idtoken2_type>

5. The CSMS responds with an AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>

6. The OCTT sends a TransactionEventRequest with
    - triggerReason StopAuthorized
    - idToken.idToken <Configured valid_idtoken2_idtoken>
    - idToken.type <Configured valid_idtoken2_type>
    - eventType Updated

7. The CSMS responds with a TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>

8. Execute Reusable State EVConnectedPostSession
9. Execute Reusable State EVDisconnected

Configuration
    VALID_ID_TOKEN / VALID_ID_TOKEN_TYPE:     first idToken with GroupId
    VALID_ID_TOKEN_2 / VALID_ID_TOKEN_TYPE_2: second idToken with same GroupId
    GROUP_ID:                                  the shared GroupId value
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
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_connected_post_session import ev_connected_post_session
from reusable_states.ev_disconnected import ev_disconnected
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, validate_schema

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_43(connection):
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
    await parking_bay_occupied(cp, evse_id=evse_id)
    await ev_connected_pre_session(cp, evse_id=evse_id, connector_id=connector_id)

    transaction_id = generate_transaction_id()

    # 1. TransactionEventRequest: Authorized with valid_idtoken
    event = TransactionEvent(
        event_type=TransactionEventType.started,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.authorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            "transaction_id": transaction_id,
            "charging_state": "EVConnected",
        },
        id_token=IdTokenType(id_token=token_id_1, type=token_type_1),
        evse={
            "id": evse_id,
            "connector_id": connector_id
        }
    )
    response_1 = await cp.send_transaction_event_request(event)

    # 2. CSMS responds: Accepted + groupIdToken
    assert response_1 is not None
    assert validate_schema(data=response_1, schema_file_name='../schema/TransactionEventResponse.json')
    assert response_1.id_token_info is not None
    assert response_1.id_token_info.status == AuthorizationStatusType.accepted
    assert response_1.id_token_info.group_id_token.id_token == group_id

    # 3. Execute Reusable State EnergyTransferStarted
    await energy_transfer_started(cp, evse_id=evse_id, connector_id=connector_id, transaction_id=transaction_id)

    # 4. AuthorizeRequest with valid_idtoken2 (same GroupId)
    auth_response = await cp.send_authorization_request(id_token=token_id_2, token_type=token_type_2)

    # 5. CSMS responds: Accepted + groupIdToken
    assert auth_response is not None
    assert validate_schema(data=auth_response, schema_file_name='../schema/AuthorizeResponse.json')
    assert auth_response.id_token_info['status'] == AuthorizationStatusType.accepted
    assert auth_response.id_token_info['group_id_token']['id_token'] == group_id

    # 6. TransactionEventRequest: StopAuthorized with valid_idtoken2
    event_stop = TransactionEvent(
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
    response_2 = await cp.send_transaction_event_request(event_stop)

    # 7. CSMS responds: Accepted + groupIdToken
    assert response_2 is not None
    assert validate_schema(data=response_2, schema_file_name='../schema/TransactionEventResponse.json')
    assert response_2.id_token_info is not None
    assert response_2.id_token_info.status == AuthorizationStatusType.accepted
    assert response_2.id_token_info.group_id_token.id_token == group_id

    # 8. Execute Reusable State EVConnectedPostSession
    await ev_connected_post_session(cp, evse_id=evse_id, connector_id=connector_id, transaction_id=transaction_id)

    # 9. Execute Reusable State EVDisconnected
    await ev_disconnected(cp, evse_id=evse_id, connector_id=connector_id, transaction_id=transaction_id)

    start_task.cancel()
