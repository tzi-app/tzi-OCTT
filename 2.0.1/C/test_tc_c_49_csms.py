"""
Test case name      Stop Transaction with a Master Pass - Without UI
Test case Id        TC_C_49_CSMS
Use case Id(s)      C16
Requirement(s)      C16.FR.02

Requirement Details:
    C16.FR.02: User presents an IdToken that has a groupId equal to MasterPassGroupId AND the Charging Station does NOT have a UI. The Charging Station SHALL stop all ongoing transactions as described in use case E07.
        Precondition: User presents an IdToken that has a groupId equal to MasterPassGroupId AND the Charging Station does NOT have a UI.
System under test   CSMS

Description         This test case covers how somebody with a Master Pass (User) can stop (selected) ongoing
                    transactions, so the cable becomes unlocked. This Master Pass can be configured in:
                    MasterPassGroupId. This could for example be useful for Law Enforcement officials.
                    Purpose To verify if the CSMS is able to correctly respond on a request to stop all transactions
                    when an idToken which has the MasterPass as GroupId is used and the Charging Station does not
                    have a User Interface according to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Before (Preparations)
    Configuration State:    N/a
    Memory State:           An idToken with the MasterPass as GroupId is configured
    Reusable State(s):
        State is EnergyTransferStarted for EVSE 1 with idToken valid_idtoken
        State is EnergyTransferStarted for EVSE 2 with idToken valid_idtoken2

Test Scenario
1. The OCTT sends an AuthorizeRequest with
    - idToken.idToken <Configured masterpass_idtoken_idtoken>
    - idToken.type <Configured masterpass_idtoken_type>

2. The CSMS responds with an AuthorizeResponse

3. The OCTT sends a TransactionEventRequest (for EVSE 1) with
    - transactionInfo.stoppedReason MasterPass
    - idToken.idToken <Configured valid_idtoken_idtoken> (original transaction token for EVSE 1)
    - idToken.type <Configured valid_idtoken_type>
    - eventType Ended

    Note: Without UI, the CS uses the original transaction token (not the masterpass) since it
    cannot display a UI selection to the user.

4. The CSMS responds with a TransactionEventResponse for EVSE 1

5. The OCTT sends a TransactionEventRequest (for EVSE 2) with
    - transactionInfo.stoppedReason MasterPass
    - idToken.idToken <Configured valid_idtoken2_idtoken> (original transaction token for EVSE 2)
    - idToken.type <Configured valid_idtoken2_type>
    - eventType Ended

6. The CSMS responds with a TransactionEventResponse for EVSE 2

Configuration
    VALID_ID_TOKEN / VALID_ID_TOKEN_TYPE:       idToken used to start EVSE 1 transaction
    VALID_ID_TOKEN_2 / VALID_ID_TOKEN_TYPE_2:   idToken used to start EVSE 2 transaction
    MASTERPASS_ID_TOKEN / MASTERPASS_ID_TOKEN_TYPE: the Master Pass idToken (GroupId = MasterPassGroupId)
    MASTERPASS_GROUP_ID:                         the MasterPass group identifier value
"""

import asyncio
import pytest
import os

from ocpp.v201.enums import (
    AuthorizationStatusEnumType as AuthorizationStatusType,
    TriggerReasonEnumType as TriggerReasonType,
    TransactionEventEnumType as TransactionEventType,
    ReasonEnumType,
)
from ocpp.v201.call import TransactionEvent
from ocpp.v201.datatypes import IdTokenType
from tzi_charge_point import TziChargePoint
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, validate_schema

BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_49(connection):
    token_id_1 = os.environ['VALID_ID_TOKEN']
    token_type_1 = os.environ['VALID_ID_TOKEN_TYPE']
    token_id_2 = os.environ['VALID_ID_TOKEN_2']
    token_type_2 = os.environ['VALID_ID_TOKEN_TYPE_2']
    masterpass_id = os.environ['MASTERPASS_ID_TOKEN']
    masterpass_type = os.environ['MASTERPASS_ID_TOKEN_TYPE']
    masterpass_group_id = os.environ['MASTERPASS_GROUP_ID']
    evse_id_1 = 1
    evse_id_2 = 2
    connector_id = 1

    assert connection.open
    cp = TziChargePoint(BASIC_AUTH_CP, connection)

    start_task = asyncio.create_task(cp.start())

    # Setup: EnergyTransferStarted for EVSE 1 (with valid_idtoken) and EVSE 2 (with valid_idtoken2)
    transaction_id_1 = generate_transaction_id()
    transaction_id_2 = generate_transaction_id()
    await energy_transfer_started(cp, evse_id=evse_id_1, connector_id=connector_id, transaction_id=transaction_id_1)
    await energy_transfer_started(cp, evse_id=evse_id_2, connector_id=connector_id, transaction_id=transaction_id_2)

    # 1. AuthorizeRequest with Master Pass idToken
    auth_response = await cp.send_authorization_request(id_token=masterpass_id, token_type=masterpass_type)

    # 2. CSMS responds with AuthorizeResponse
    assert auth_response is not None
    assert validate_schema(data=auth_response, schema_file_name='../schema/AuthorizeResponse.json')
    assert auth_response.id_token_info['status'] == AuthorizationStatusType.accepted
    assert auth_response.id_token_info['group_id_token']['id_token'] == masterpass_group_id

    # 3. TransactionEventRequest: Ended for EVSE 1 with the ORIGINAL transaction idToken (valid_idtoken)
    #    Without UI: CS uses the original transaction token, not the masterpass token
    event_end_1 = TransactionEvent(
        event_type=TransactionEventType.ended,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.stop_authorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            "transaction_id": transaction_id_1,
            "charging_state": "Idle",
            "stopped_reason": ReasonEnumType.master_pass,
        },
        id_token=IdTokenType(id_token=token_id_1, type=token_type_1),
        evse={
            "id": evse_id_1,
            "connector_id": connector_id
        }
    )
    response_1 = await cp.send_transaction_event_request(event_end_1)

    # 4. CSMS responds with TransactionEventResponse for EVSE 1
    assert response_1 is not None
    assert validate_schema(data=response_1, schema_file_name='../schema/TransactionEventResponse.json')
    assert response_1.id_token_info is not None
    assert response_1.id_token_info.status == AuthorizationStatusType.accepted
    assert response_1.id_token_info.group_id_token.id_token == masterpass_group_id

    # 5. TransactionEventRequest: Ended for EVSE 2 with the ORIGINAL transaction idToken (valid_idtoken2)
    event_end_2 = TransactionEvent(
        event_type=TransactionEventType.ended,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.stop_authorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            "transaction_id": transaction_id_2,
            "charging_state": "Idle",
            "stopped_reason": ReasonEnumType.master_pass,
        },
        id_token=IdTokenType(id_token=token_id_2, type=token_type_2),
        evse={
            "id": evse_id_2,
            "connector_id": connector_id
        }
    )
    response_2 = await cp.send_transaction_event_request(event_end_2)

    # 6. CSMS responds with TransactionEventResponse for EVSE 2
    assert response_2 is not None
    assert validate_schema(data=response_2, schema_file_name='../schema/TransactionEventResponse.json')
    assert response_2.id_token_info is not None
    assert response_2.id_token_info.status == AuthorizationStatusType.accepted
    assert response_2.id_token_info.group_id_token.id_token == masterpass_group_id

    start_task.cancel()
