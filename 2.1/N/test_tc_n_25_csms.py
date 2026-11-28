"""
Test case name      Retrieve Log Information - Diagnostics Log - Success
Test case Id        TC_N_25_CSMS
Use case Id(s)      N01
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers the functionality of getting log information from a Charging
                    Station. The CSMS can request a Charging Station to upload a file with log information to
                    a given location (URL). The format of this log file is not prescribed. The Charging
                    Station successfully uploads a log file and gives information about the status of the
                    upload by sending status notifications to the CSMS.

Purpose             To verify if the CSMS is able to request a charging station to successfully upload a log
                    as described at the OCPP specification.

Prerequisite(s)     Charging Station has log information available.

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetLogRequest
2. The Test System responds with a GetLogResponse with status Accepted
3. The Test System sends a LogStatusNotificationRequest with
    - status Uploading
    - requestId Same Id as the GetLogRequest
4. The CSMS responds with a LogStatusNotificationResponse.
5. The Test System sends a LogStatusNotificationRequest with
    - status Uploaded
    - requestId Same Id as the GetLogRequest
6. The CSMS responds with a LogStatusNotificationResponse.

Tool validations
* Step 1:
    Message GetLogRequest
    - logType DiagnosticsLog

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from diagnostics import request_log
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_25(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: Charging Station has log information available.
    # 1. The CSMS sends a GetLogRequest
    # 2. The Test System responds with a GetLogResponse with status Accepted
    request = await request_log(cp, 'DiagnosticsLog')
    assert request.log_type == 'DiagnosticsLog', \
        f"Expected GetLogRequest.logType DiagnosticsLog, got {request.log_type}"

    # 3. The Test System sends a LogStatusNotificationRequest with
    #    - status Uploading
    #    - requestId Same Id as the GetLogRequest
    # 4. The CSMS responds with a LogStatusNotificationResponse.
    # 5. The Test System sends a LogStatusNotificationRequest with
    #    - status Uploaded
    #    - requestId Same Id as the GetLogRequest
    # 6. The CSMS responds with a LogStatusNotificationResponse.
    for status in ('Uploading', 'Uploaded'):
        await cp.send_log_status_notification_request(status, request_id=request.request_id)

    start_task.cancel()
