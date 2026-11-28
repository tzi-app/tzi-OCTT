"""
Test case name      Retrieve Log Information - DataCollectorLog - Success
Test case Id        TC_N_100_CSMS
Use case Id(s)      N01
Requirement(s)      …
System under test   Charging Station

Description         This test case covers the functionality of getting log information from a Charging
                    Station. The CSMS can request a Charging Station to upload a file with log information to
                    a given location (URL). The format of this log file is not prescribed. The Charging
                    Station successfully uploads a log file and gives information about the status of the
                    upload by sending status notifications to the CSMS.

Purpose             To verify if the CSMS is able to successfully retrieve a log of logType DataCollectorLog
                    as described at the OCPP specification.

Prerequisite(s)     - CSMS supports DataCollectorLog.
                    - A diagnostics logging server has been setup supporting one of the file transfer
                      protocols supported by the Charging Station (This is configured at the configuration
                      variable FileTransferProtocols).
                    - Charging station supports DataCollector (Component DataCollector available).

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to retrieve the DataCollectorLog

1. The CSMS sends a GetLogRequest
2. The Test System responds with a GetLogResponse
3. The Test System sends a LogStatusNotificationRequest with
    - status Uploading
    - requestId <GetLogRequest.requestId of step 1>
4. The CSMS responds with a LogStatusNotificationResponse .
5. The Test System sends a LogStatusNotificationRequest with
    - status Uploaded
    - requestId <GetLogRequest.requestId of step 1>
6. The CSMS responds with a LogStatusNotificationResponse .

Tool validations
* Step 1:
    Message GetLogRequest
    - logType DataCollectorLog

Post scenario validations:
    N/a
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
async def test_tc_n_100(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisite: Charging station supports DataCollector (Component DataCollector available).
    cp.variables = {'DataCollector.Available': 'true', 'DataCollector.Enabled': 'true'}
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to retrieve the DataCollectorLog
    # 1. The CSMS sends a GetLogRequest
    # 2. The Test System responds with a GetLogResponse
    request = await request_log(cp, 'DataCollectorLog')
    assert request.log_type == 'DataCollectorLog', \
        f"Expected GetLogRequest.logType DataCollectorLog, got {request.log_type}"

    # 3. The Test System sends a LogStatusNotificationRequest with
    #    - status Uploading
    #    - requestId <GetLogRequest.requestId of step 1>
    # 4. The CSMS responds with a LogStatusNotificationResponse.
    # 5. The Test System sends a LogStatusNotificationRequest with
    #    - status Uploaded
    #    - requestId <GetLogRequest.requestId of step 1>
    # 6. The CSMS responds with a LogStatusNotificationResponse.
    for status in ('Uploading', 'Uploaded'):
        await cp.send_log_status_notification_request(status, request_id=request.request_id)

    start_task.cancel()
