"""
Test case name      Send Local Authorization List - Differential Remove
Test case Id        TC_D_03_CSMS
Use case Id(s)      D01
Requirement(s)      D01_FR_01, D01_FR_06, D01_FR_18, D01_FR_17

Requirement Details:
    D01.FR.01: SendLocalListRequest SHALL contain the type of update (updateType) and a version number
               (versionNumber) that the Charging Station MUST associate with the Local Authorization List
               after it has been updated.
    D01.FR.06: All IdTokens in the Local Authorization List SHALL be unique.
        Note: No duplicate values are allowed.
    D01.FR.18: versionNumber in a SendLocalListRequest SHALL be greater than 0.
        Note: In GetLocalListVersionResponse the versionNumber = 0 has a special meaning: No Local List
              installed. So the value 0 should never be used.
    D01.FR.17: The Charging Station SHALL remove these elements from its Local Authorization List and set the
               version number to the value specified in the message.
        Precondition: If the Charging Station receives a SendLocalListRequest with updateType is Differential
                      AND localAuthorizationList contains AuthorizationData elements without idTokenInfo
System under test   CSMS

Description         The CSMS sends a Local Authorization List which a Charging Station can use for the
                    authorization of idTokens. The list MAY be either a full list to replace the current list
                    in the Charging Station or it MAY be a differential list with updates to be applied to the
                    current list in the Charging Station.

Purpose             To verify if the CSMS is able to send a Differential Local Authorization List with data
                    without idToken according to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to send a Local Authorization list to the Charging Station with type
               Differential and AuthorizationData elements without idTokenInfo in the message

1. The CSMS sends a SendLocalListRequest
2 The Test System responds with a SendLocalListResponse with status Accepted

Note(s): If the Local Authorization List is too big for one message, step 1 and 2 will be repeated

Tool validations
* Step 1:
    Message SendLocalListRequest
    - updateType Differential
    - versionNumber <Bigger than currently configured in Test System>
    - localAuthorizationList <AuthorizationData elements without idTokenInfo>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
LOCAL_LIST_VERSION = int(os.environ['LOCAL_LIST_VERSION'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_d_03(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    cp.local_list_version = LOCAL_LIST_VERSION
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to send a Local Authorization list to the Charging
    #                Station with type Differential and AuthorizationData elements without
    #                idTokenInfo in the message
    # 1. The CSMS sends a SendLocalListRequest
    # 2. The Test System responds with a SendLocalListResponse with status Accepted
    request = await cp.wait_for_request(
        'SendLocalList',
        manual_action=send_call(BASIC_AUTH_CP, 'SendLocalList', {
            'versionNumber': LOCAL_LIST_VERSION + 1,
            'updateType': 'Differential',
            'localAuthorizationList': [
                {'idToken': {'idToken': 'D001001', 'type': 'Central'}},
            ],
        }))

    assert request.update_type == 'Differential', \
        f"Expected updateType Differential, got: {request.update_type}"
    assert request.version_number > LOCAL_LIST_VERSION, \
        f"Expected versionNumber bigger than the {LOCAL_LIST_VERSION} of the Test System, " \
        f"got: {request.version_number}"
    # localAuthorizationList: AuthorizationData elements without idTokenInfo (D01.FR.17: the
    # station removes these idTokens from its list)
    assert request.local_authorization_list, "Expected AuthorizationData elements in localAuthorizationList"
    for index, authorization_data in enumerate(request.local_authorization_list):
        assert authorization_data.id_token_info is None, \
            f"localAuthorizationList[{index}] has an idTokenInfo: {authorization_data}"

    start_task.cancel()
