"""
Test case name      Send Local Authorization List - Differential
Test case Id        TC_043_5_CSMS
System under test   Central System
Document ref        Section 3.14.2, Table 160, pages 137-138/176
                    (OCPP Compliancy Testing Tool - TestCaseDocument, 2025-11)

Description         The Charge Point can authorize an EV driver based on a local list that is set by
                    the Central System.

Purpose             Check whether a Local Authorization List can be sent to a Charge Point to
                    authorize an EV driver.

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile and
                    has at least 1 IdToken to add to the local authorization list.

Before
    Configuration State(s): n/a
    Memory State(s):
        Set the initial local authorization list using update type full.
    Reusable State(s): n/a

Test Scenario
1. The Central System sends a GetLocalListVersion.req to the Charge Point.
2. The Charge Point responds with a GetLocalListVersion.conf.
   (Note: Messages 1 and 2 are optional.)
   Manual Action: Trigger the Central System to send a SendLocalList updateType Differential
   for a specific idToken that is not already part of the list.
3. The Central System sends a SendLocalList.req.
4. The Charge Point responds with a SendLocalList.conf.

Tool validations
    * Step 2: (Message: GetLocalListVersion.conf)
        - listVersion is <Provided listVersion by Central System>.
    * Step 3: (Message: SendLocalList.req)
        - updateType should be Differential.
        - localAuthorizationList contains <Only the specified idToken, including an idTagInfo.>
          NOTE: "Only the specified idToken" suggests exactly 1 entry. The test validates at least 1
          entry with idTagInfo but does not enforce exactly 1, since the CSMS may batch entries.
        - versionNumber should be <Greater than the initial listVersion.>
    * Step 4: (Message: SendLocalList.conf)
        - status is Accepted.

Implementation notes
    - Steps 1-2 (GetLocalListVersion) are marked optional in the spec but this test requires them.
      If the CSMS skips GetLocalListVersion, the test will timeout. This is acceptable as long as
      the CSMS always sends GetLocalListVersion before a Differential update.

Expected result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import UpdateStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_043_5(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # Report existing list version = 1
    cp._local_list_version = 1
    # CP responds Accepted for the differential SendLocalList
    cp._send_local_list_response_status = UpdateStatus.accepted
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send GetLocalListVersion.req → CP responds with listVersion=1
    await asyncio.wait_for(cp._received_get_local_list_version.wait(), timeout=ACTION_TIMEOUT)

    # Reset the event to wait for the next CSMS-initiated message (SendLocalList)
    cp._received_send_local_list.clear()

    # Step 3-4: Wait for CSMS to send SendLocalList.req (Differential) → CP responds Accepted
    await asyncio.wait_for(cp._received_send_local_list.wait(), timeout=ACTION_TIMEOUT)
    # Validate updateType is Differential
    assert cp._send_local_list_data['update_type'] == 'Differential'

    # Validate versionNumber > initial listVersion (1)
    assert cp._send_local_list_data['list_version'] > 1, \
        f"versionNumber should be > 1, got {cp._send_local_list_data['list_version']}"

    # Validate localAuthorizationList contains entries with idTagInfo
    auth_list = cp._send_local_list_data.get('local_authorization_list') or []
    assert len(auth_list) > 0, "localAuthorizationList should not be empty"
    for entry in auth_list:
        assert 'id_tag_info' in entry, f"Entry missing idTagInfo: {entry}"

    start_task.cancel()
