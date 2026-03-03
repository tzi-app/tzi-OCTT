"""
Test case name      Stop Transaction with a Master Pass - With UI - Specific transactions
Test case Id        TC_C_48_CSMS
Use case Id(s)      C16
Requirement(s)      C16.FR.01

Requirement Details:
    C16.FR.01: User presents an IdToken that has a groupId equal to MasterPassGroupId AND The Charging Station has a UI with input capabilities. The Charging Station SHALL "show" the Master Pass UI to let user select which transaction to stop.
        Precondition: User presents an IdToken that has a groupId equal to MasterPassGroupId AND The Charging Station has a UI with input capabilities.
System under test   CSMS

Description         This test case covers how somebody with a Master Pass (User) can stop (selected) ongoing
                    transactions, so the cable becomes unlocked. This Master Pass can be configured in:
                    MasterPassGroupId. This could for example be useful for Law Enforcement officials.
                    Purpose To verify if the CSMS is able to correctly respond on a request to stop a transaction
                    when an idToken which has the MasterPass as GroupId is used and the user has selected to stop
                    one transaction in the User Interface according to the mechanism as described in the OCPP
                    specification.

Prerequisite(s)     N/a

Before (Preparations)
    Configuration State:    N/a
    Memory State:           An idToken with the MasterPass as GroupId is configured
    Reusable State(s):      State is EnergyTransferStarted for all EVSE

Test Scenario
1. The OCTT sends an AuthorizeRequest with
    - idToken.idToken <Configured valid_idtoken_idtoken> (idToken whose GroupId = MasterPassGroupId)
    - idToken.type <Configured valid_idtoken_type>

2. The CSMS responds with an AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured masterPassGroupId>

3. The OCTT sends a TransactionEventRequest with
    - transactionInfo.stoppedReason MasterPass
    - idToken.idToken <Configured masterpass_idtoken_idtoken>
    - idToken.type <Configured masterpass_idtoken_type>
    - eventType Ended

4. The CSMS responds with a TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured masterPassGroupId>

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured masterPassGroupId>
* Step 4:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured masterPassGroupId>

Configuration
    VALID_ID_TOKEN / VALID_ID_TOKEN_TYPE:           idToken with MasterPass as GroupId
    MASTERPASS_ID_TOKEN / MASTERPASS_ID_TOKEN_TYPE: the Master Pass idToken used to stop the transaction
    MASTERPASS_GROUP_ID:                             the MasterPass group identifier value
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
async def test_tc_c_48(connection):
    token_id_1 = os.environ['VALID_ID_TOKEN']
    token_type_1 = os.environ['VALID_ID_TOKEN_TYPE']
    masterpass_id = os.environ['MASTERPASS_ID_TOKEN']
    masterpass_type = os.environ['MASTERPASS_ID_TOKEN_TYPE']
    masterpass_group_id = os.environ['MASTERPASS_GROUP_ID']
    evse_id = 1
    connector_id = 1

    assert connection.open
    cp = TziChargePoint(BASIC_AUTH_CP, connection)

    start_task = asyncio.create_task(cp.start())

    # Setup: EnergyTransferStarted for EVSE 1
    transaction_id = generate_transaction_id()
    await energy_transfer_started(cp, evse_id=evse_id, connector_id=connector_id, transaction_id=transaction_id)

    # 1. AuthorizeRequest with valid_idtoken (whose GroupId = MasterPassGroupId)
    auth_response = await cp.send_authorization_request(id_token=token_id_1, token_type=token_type_1)

    # 2. CSMS responds: Accepted + groupIdToken = masterPassGroupId
    assert auth_response is not None
    assert validate_schema(data=auth_response, schema_file_name='../schema/AuthorizeResponse.json')
    assert auth_response.id_token_info['status'] == AuthorizationStatusType.accepted
    assert auth_response.id_token_info['group_id_token']['id_token'] == masterpass_group_id

    # 3. TransactionEventRequest: Ended with masterpass_idtoken (user selected to stop this specific transaction)
    event_end = TransactionEvent(
        event_type=TransactionEventType.ended,
        timestamp=now_iso(),
        trigger_reason=TriggerReasonType.stop_authorized,
        seq_no=cp.next_seq_no(),
        transaction_info={
            "transaction_id": transaction_id,
            "charging_state": "Idle",
            "stopped_reason": ReasonEnumType.master_pass,
        },
        id_token=IdTokenType(id_token=masterpass_id, type=masterpass_type),
        evse={
            "id": evse_id,
            "connector_id": connector_id
        }
    )
    response = await cp.send_transaction_event_request(event_end)

    # 4. CSMS responds: Accepted + groupIdToken = masterPassGroupId
    assert response is not None
    assert validate_schema(data=response, schema_file_name='../schema/TransactionEventResponse.json')
    assert response.id_token_info is not None
    assert response.id_token_info.status == AuthorizationStatusType.accepted
    assert response.id_token_info.group_id_token.id_token == masterpass_group_id

    start_task.cancel()
