"""
Test case name      Send Local Authorization List - Full
Test case Id        TC_D_01_CSMS
Use case Id(s)      D01
Requirement(s)      D01_FR_01, D01_FR_06, D01_FR_18

Requirement Details:
    D01.FR.01: SendLocalListRequest SHALL contain the type of update (updateType) and a version number
               (versionNumber) that the Charging Station MUST associate with the Local Authorization List
               after it has been updated.
    D01.FR.06: All IdTokens in the Local Authorization List SHALL be unique.
        Note: No duplicate values are allowed.
    D01.FR.18: versionNumber in a SendLocalListRequest SHALL be greater than 0.
        Note: In GetLocalListVersionResponse the versionNumber = 0 has a special meaning: No Local List
              installed. So the value 0 should never be used.
System under test   CSMS

Description         The CSMS sends a Local Authorization List which a Charging Station can use for the
                    authorization of idTokens. The list MAY be either a full list to replace the current list
                    in the Charging Station or it MAY be a differential list with updates to be applied to the
                    current list in the Charging Station.

Purpose             To verify if the CSMS is able to send a Full Local Authorization List according to the
                    mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetLocalListVersionRequest
2. The Test System responds with a GetLocalListVersionResponse with versionNumber 1

Note(s): This step is optional

3. The CSMS sends a SendLocalListRequest
4. The Test System responds with a SendLocalListResponse with status Accepted

Note(s): If the Local Authorization List is too big for one message, step 1 and 2 will be repeated

Tool validations
* Step 1:
    Message SendLocalListRequest
    - updateType Full
    - versionNumber <Bigger than 0>
    - localAuthorizationList <Not empty>
    - localAuthorizationList[n].idTokenInfo <Not empty>

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
async def test_tc_d_01(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # 1. The CSMS sends a GetLocalListVersionRequest
    # 2. The Test System responds with a GetLocalListVersionResponse with versionNumber 1
    # This step is optional: when the CSMS asks for the version, the station answers it.
    cp.local_list_version = LOCAL_LIST_VERSION
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 3. The CSMS sends a SendLocalListRequest
    # 4. The Test System responds with a SendLocalListResponse with status Accepted
    request = await cp.wait_for_request(
        'SendLocalList',
        manual_action=send_call(BASIC_AUTH_CP, 'SendLocalList', {
            'versionNumber': LOCAL_LIST_VERSION + 1,
            'updateType': 'Full',
            'localAuthorizationList': [
                {
                    'idToken': {'idToken': 'D001001', 'type': 'Central'},
                    'idTokenInfo': {'status': 'Accepted'},
                },
                {
                    'idToken': {'idToken': 'D001002', 'type': 'Central'},
                    'idTokenInfo': {'status': 'Accepted'},
                },
            ],
        }))

    assert request.update_type == 'Full', f"Expected updateType Full, got: {request.update_type}"
    assert request.version_number > 0, f"Expected versionNumber > 0, got: {request.version_number}"
    assert request.local_authorization_list, "Expected a localAuthorizationList that is not empty"
    for index, authorization_data in enumerate(request.local_authorization_list):
        assert authorization_data.id_token_info, \
            f"localAuthorizationList[{index}] has no idTokenInfo: {authorization_data}"

    start_task.cancel()
