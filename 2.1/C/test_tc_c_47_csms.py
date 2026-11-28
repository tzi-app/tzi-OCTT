"""
Test case name      Stop Transaction with a Master Pass - With UI - All transactions
Test case Id        TC_C_47_CSMS
Use case Id(s)      C16
Requirement(s)      C16_FR_01

Requirement Details:
    C16.FR.01: The Charging Station SHALL "show" the Master Pass UI to let user select which transaction to
               stop.
        Precondition: User presents an IdToken that has a groupId equal to MasterPassGroupId AND The Charging
                      Station has a UI with input capabilities.
System under test   CSMS

Description         This test case covers how somebody with a Master Pass (User) can stop (selected) ongoing
                    transactions, so the cable becomes unlocked. This Master Pass can be configured in:
                    MasterPassGroupId. This could for example be usefull for Law Enforcement officials.

Purpose             To verify if the CSMS is able to correctly respond on a request to stop all transactions
                    when an idToken which has the MasterPass as GroupId is used and the user has selected to
                    stop all transactions in the User Interface according to the mechanism as described in the
                    OCPP specification.

Prerequisite(s)     - N/a

Configuration State N/a

Memory State        An idToken with the MastersPass as GroupId is configured

Reusable State(s)   State is EnergyTransferStarted for EVSE 1 with idToken valid idToken
                    State is EnergyTransferStarted for EVSE 2 with idToken valid idToken2

Test Scenario
1. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured masterpass_idtoken_idtoken>
    - idToken.type <Configured masterpass_idtoken_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System sends a TransactionEventRequest with
    - transactionInfo.stoppedReason MasterPass
    - idToken.idToken <Configured masterpass_idtoken_idtoken>
    - idToken.type <Configured masterpass_idtoken_type>
    - eventType Ended
    for both EVSE
4. The CSMS responds with a TransactionEventResponse for both EVSE

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured masterPassGroupId>
* Step 4:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured masterPassGroupId>

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.1. Page 1022 - 1024 - (2026-04) - TC_C_47_CSMS/TC_C_48_CSMS/TC_C_49_CSMS - Removed configuration
        variable masterPassGroupId
        The <Configured MasterPassGroupId> variable has been removed from the OCTT. The MasterPassGroupId can
        be provided to the OCTT by the CSMS through a SetVariableRequest.

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | Manual action : trigger CSMS to set the masterPassGroupId | |
        | 2. The Charging Station responds with SetVariablesResponse with attributeStatus = Accepted | 1. Test
          System sends SetVariablesRequest with: / - variable.name = "MasterPassGroupId" / - component.name =
          "AuthCtrlr" / - attributeValue = <Specified masterPassGroupId> |

        Where applicable tool validations mentioning <Configured masterPassGroupId> were replace with the
        masterPassGroupId specified through the SetVariablesRequest

        | Tool validations |
        | \\* Step 4: / Message AuthorizeResponse / - idTokenInfo.groupIdToken.idToken [removed: <Configured
          masterPassGroupId>] <masterPassGroupId from step 1> / \\* Step 6: / Message TransactionEventResponse
          / - idTokenInfo.groupIdToken.idToken [removed: <Configured masterPassGroupId>] <masterPassGroupId
          from step 1> |
        | Post scenario validations: / - N/a |
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import set_master_pass_group_id, validate_id_token_info
from charge_point import ChargingSession, TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
VALID_ID_TOKEN_2 = os.environ['VALID_ID_TOKEN_2']
VALID_ID_TOKEN_TYPE_2 = os.environ['VALID_ID_TOKEN_TYPE_2']
# Memory State: An idToken with the MasterPass as GroupId is configured
MASTERPASS_ID_TOKEN = {'id_token': os.environ['MASTERPASS_ID_TOKEN'],
                       'type': os.environ['MASTERPASS_ID_TOKEN_TYPE']}


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_47(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State(s): State is EnergyTransferStarted for EVSE 1 with idToken valid idToken
    #                    State is EnergyTransferStarted for EVSE 2 with idToken valid idToken2
    sessions = [ChargingSession(), ChargingSession()]
    await energy_transfer_started(
        cp, evse_id=1, connector_id=CONFIGURED_CONNECTOR_ID,
        id_token=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE, session=sessions[0])
    await energy_transfer_started(
        cp, evse_id=2, connector_id=CONFIGURED_CONNECTOR_ID,
        id_token=VALID_ID_TOKEN_2, id_token_type=VALID_ID_TOKEN_TYPE_2, session=sessions[1])

    # Errata 2026-09 (6.3.1), new steps 1-2: the CSMS sets the masterPassGroupId with a
    # SetVariablesRequest. The steps below are the steps 3-6 of the errata.
    master_pass_group_id = await set_master_pass_group_id(cp)

    # 1. The Test System sends an AuthorizeRequest with
    #    - idToken.idToken <Configured masterpass_idtoken_idtoken>
    #    - idToken.type <Configured masterpass_idtoken_type>
    # 2. The CSMS responds with an AuthorizeResponse
    response = await cp.call(call.Authorize(id_token=MASTERPASS_ID_TOKEN))
    validate_id_token_info('AuthorizeResponse', response.id_token_info,
                           status='Accepted', group_id=master_pass_group_id)

    # 3. The Test System sends a TransactionEventRequest with
    #    - transactionInfo.stoppedReason MasterPass
    #    - idToken.idToken <Configured masterpass_idtoken_idtoken>
    #    - idToken.type <Configured masterpass_idtoken_type>
    #    - eventType Ended
    #    for both EVSE
    # 4. The CSMS responds with a TransactionEventResponse for both EVSE
    for session in sessions:
        response = await cp.call(call.TransactionEvent(
            event_type='Ended',
            timestamp=utc_now_iso(),
            trigger_reason='StopAuthorized',
            seq_no=session.next_seq_no(),
            transaction_info={
                'transaction_id': session.transaction_id,
                'stopped_reason': 'MasterPass',
            },
            id_token=MASTERPASS_ID_TOKEN,
        ))
        validate_id_token_info('TransactionEventResponse', response.id_token_info,
                               status='Accepted', group_id=master_pass_group_id)

    start_task.cancel()
