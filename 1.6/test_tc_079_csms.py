"""
Test case name      Get Security Log
Test case Id        TC_079_CSMS
Section             3.21.2 Security event/logging
System under test   Central System
Reference           CompliancyTestTool-TestCaseDocument, Table 191, Page 164

Description         The Charge Point uploads a security log to a specified location based on a request of the Central System.

Purpose             To check whether Central System can trigger a Charge Point to upload its security log.

Prerequisite(s)     The Central System supports a security profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a GetLog.req
    2. The Charge Point responds with a GetLog.conf

    [The Charge Point starts uploading the security log.]
    3. The Charge Point sends a LogStatusNotification.req
    4. The Central System responds with a LogStatusNotification.conf

    [The Charge Point has finished uploading the security log.]
    5. The Charge Point sends a LogStatusNotification.req
    6. The Central System responds with a LogStatusNotification.conf

Tool Validations
    * Step 1:
        (Message: GetLog.req)
        The log.remoteLocation is <Configured log location>
        The logType is SecurityLog

    * Step 2:
        (Message: GetLog.conf)
        The status is Accepted

    * Step 3:
        (Message: LogStatusNotification.req)
        The status is Uploading

    * Step 5:
        (Message: LogStatusNotification.req)
        The status is Uploaded

Expected result(s) / behaviour: n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import UploadLogStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_079(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send GetLog.req
    await asyncio.wait_for(cp._received_get_log.wait(), timeout=ACTION_TIMEOUT)
    assert cp._get_log_data is not None
    assert cp._get_log_data['log_type'] == 'SecurityLog'
    request_id = cp._get_log_data['request_id']

    # Step 3-4: CP sends LogStatusNotification (Uploading)
    await cp.send_log_status_notification(
        status=UploadLogStatus.uploading,
        request_id=request_id,
    )

    # Step 5-6: CP sends LogStatusNotification (Uploaded)
    await cp.send_log_status_notification(
        status=UploadLogStatus.uploaded,
        request_id=request_id,
    )

    start_task.cancel()
