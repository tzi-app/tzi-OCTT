"""
Test case name      Clear Customer Information - Update Local Authorization List
Test case Id        TC_N_46_CSMS
Use case Id(s)      N10
Requirement(s)      N10.FR.02, N10.FR.08, D01.FR.01, D01.FR.06, D01.FR.18,

Requirement Details:
    N10.FR.02: The CSMS SHALL update the Local Authorization List using the SendLocalListRequest (see D01 -
               Send Local Authorization List).
        Precondition: When the Customer referred to by the customer identifier is present in the Local
                      Authorization List of a Charging Station
        Note: To prevent problems with Local Authorization List versions.
    N10.FR.08: The CSMS SHALL include a reference to a customer by including either an idToken,
               customerCertificate or customerIdentifier in the CustomerInformationRequest.
    D01.FR.01: SendLocalListRequest SHALL contain the type of update (updateType) and a version number
               (versionNumber) that the Charging Station MUST associate with the Local Authorization List
               after it has been updated.
    D01.FR.06: All IdTokens in the Local Authorization List SHALL be unique.
        Note: No duplicate values are allowed.
    D01.FR.18: versionNumber in a SendLocalListRequest SHALL be greater than 0.
        Note: In GetLocalListVersionResponse the versionNumber = 0 has a special meaning: No Local List
              installed. So the value 0 should never be used.
System under test   CSMS

Description         The CSMS sends a message to the Charging Station to clear (and retrieve) raw customer
                    information, for example to be compliant with local privacy laws. The Charging Station
                    notifies the CSMS by sending one or more reports.

Purpose             To verify if the CSMS updates the local authorization list when customer information,
                    which was present in the local authorization list, has been removed as described at the
                    OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        A local authorization list with <Configured valid_idtoken_idtoken> is configured.

Reusable State      N/a

Test Scenario
Manual action: Trigger CSMS to CustomerInformationRequest to both report and clear token <Configured
               valid_idtoken_idtoken> and <Configured valid_idtoken_type>

1. The CSMS sends a CustomerInformationRequest
2. The Test System responds with a CustomerInformationResponse
    with status Accepted
3. The Test System sends a NotifyCustomerInformationRequest
4. The CSMS responds with a NotifyCustomerInformationResponse .

Manual action: If not triggered automatically, trigger CSMS to send SendLocalListRequest
with version = <configured local list version> + 1
and updateType = Differential
and localAuthorizationList = [{idToken = {<Configured_valid_idtoken>, <Configured valid_idtoken_type>} }]

5. The CSMS sends a SendLocalListRequest
6 The Test System responds with a SendLocalListResponse with status Accepted

Tool validations
* Step 1:
    Message CustomerInformationRequest
    - report true AND
    - clear true AND
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
* Step 5:
    Message SendLocalListRequest
    - updateType Differential
    - versionNumber <configured local list version> + 1
    - localAuthorizationListp[0].idToken contains <configured_valid_idtoken_idtoken> and <configured
      valid_idtoken_type>
    - localAuthorizationList[0].idTokenInfo <omitted>

Post scenario validations:
    - All messages have been received
"""

import asyncio
import os

import pytest

from charge_point import NO_ACTION_WAIT, TziChargePoint21
from diagnostics import request_customer_information, validate_customer_information
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = {'idToken': os.environ['VALID_ID_TOKEN'], 'type': os.environ['VALID_ID_TOKEN_TYPE']}
LOCAL_LIST_VERSION = int(os.environ['LOCAL_LIST_VERSION'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_46(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Memory State: A local authorization list with <Configured valid_idtoken_idtoken> is
    # configured.
    cp.local_list_version = LOCAL_LIST_VERSION
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual action: Trigger CSMS to CustomerInformationRequest to both report and clear token
    #                <Configured valid_idtoken_idtoken> and <Configured valid_idtoken_type>
    # 1. The CSMS sends a CustomerInformationRequest
    # 2. The Test System responds with a CustomerInformationResponse with status Accepted
    cp.forget_requests('SendLocalList')
    request = await request_customer_information(cp, report=True, clear=True, id_token=VALID_ID_TOKEN)
    validate_customer_information(request, report=True, clear=True, id_token=VALID_ID_TOKEN)

    # 3. The Test System sends a NotifyCustomerInformationRequest
    # 4. The CSMS responds with a NotifyCustomerInformationResponse.
    await cp.send_notify_customer_information(
        data=f"idToken {VALID_ID_TOKEN['idToken']}: 1 entry in the Local Authorization List",
        seq_no=0, request_id=request.request_id)

    # Manual action: If not triggered automatically, trigger CSMS to send SendLocalListRequest
    #     with version = <configured local list version> + 1
    #     and updateType = Differential
    #     and localAuthorizationList = [{idToken = {<Configured_valid_idtoken>, <Configured
    #     valid_idtoken_type>} }]
    # 5. The CSMS sends a SendLocalListRequest
    # 6. The Test System responds with a SendLocalListResponse with status Accepted
    cp.set_response('SendLocalList', status='Accepted')
    try:
        send_local_list = await cp.wait_for_request('SendLocalList', timeout=NO_ACTION_WAIT)
    except asyncio.TimeoutError:
        send_local_list = await cp.wait_for_request(
            'SendLocalList',
            manual_action=send_call(BASIC_AUTH_CP, 'SendLocalList', {
                'versionNumber': LOCAL_LIST_VERSION + 1,
                'updateType': 'Differential',
                'localAuthorizationList': [{'idToken': VALID_ID_TOKEN}],
            }))
    assert send_local_list.update_type == 'Differential', \
        f"Expected SendLocalListRequest.updateType Differential, got {send_local_list.update_type}"
    assert send_local_list.version_number == LOCAL_LIST_VERSION + 1, \
        f"Expected SendLocalListRequest.versionNumber {LOCAL_LIST_VERSION + 1}, " \
        f"got {send_local_list.version_number}"
    entries = send_local_list.local_authorization_list
    assert entries, "SendLocalListRequest has no localAuthorizationList"
    assert entries[0].id_token.id_token == VALID_ID_TOKEN['idToken'] \
        and entries[0].id_token.type == VALID_ID_TOKEN['type'], \
        f"Expected localAuthorizationList[0].idToken {VALID_ID_TOKEN}, got {entries[0].id_token}"
    assert entries[0].id_token_info is None, \
        f"localAuthorizationList[0].idTokenInfo must be omitted, got {entries[0].id_token_info}"

    start_task.cancel()
