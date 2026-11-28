"""
Test case name      Retrieve Log Information - Authentication - HTTPS
Test case Id        TC_N_103_CSMS
Use case Id(s)      N01
Requirement(s)      N01.FR.26, N01.FR.27, N01.FR.28

Requirement Details:
    N01.FR.26 (2.1): The CSMS SHALL NOT send a log upload URL that points to a server responding with a
                     redirection.
        Precondition: N01.FR.18
    N01.FR.27 (2.1): The CSMS SHALL NOT send a log upload URL containing a fragment component.
        Precondition: N01.FR.18
        Note: The fragment component would not be part of the HTTP request, so it serves no purpose.
    N01.FR.28 (2.1): The CSMS SHALL NOT include a query component that ends with a slash character ("/").
        Precondition: N01.FR.18 AND the CSMS includes a query component in the log upload URL
        Note: This is to simplify processing of the URL string in the Charging Station.
System under test   CSMS

Description         This test case covers the functionality of getting log information from a Charging
                    Station. The CSMS can request a Charging Station to upload a file with log information to
                    a given location (URL). The format of this log file is not prescribed. The Charging
                    Station successfully uploads a log file and gives information about the status of the
                    upload by sending status notifications to the CSMS.

Purpose             To verify if the CSMS is able to successfully request and process a log of logType
                    DiagnosticsLog as described at the OCPP specification.

Prerequisite(s)     - CSMS supports HTTPS file transfer protocol.
                    - A diagnostics logging server has been set up for HTTPS and accepts specific userinfo
                      credentials .

Configuration State CSMS configured to prevent unauthorised uploading to HTTPS log location.

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Trigger CSMS to GetLogRequest with logType DiagnosticsLog and remoteLocation with userinfo for
               HTTP Basic Authentication

1. CSMS sends a GetLogRequest
2. Test System responds with a GetLogResponse with
    - status Accepted
3. The Test System uploads log file to <GetLogRequest.log.remoteLocation of step 1> using HTTP POST
4. The CSMS responds using HTTP
5. The Test System uploads file to <GetLogRequest.log.remoteLocation of step 1> using HTTP POST
6. The CSMS responds using HTTP
7. Test System sends a LogStatusNotificationRequest with
    - status Uploading
    - requestId <GetLogRequest.requestId of step 1>
8. CSMS responds with a LogStatusNotificationResponse
9. Test System sends a LogStatusNotificationRequest with
    - status Uploaded
    - requestId <GetLogRequest.requestId of step 1>
10. CSMS responds with a LogStatusNotificationResponse

Tool validations
* Step 1:
    Message GetLogRequest
    - logType must be DiagnosticsLog
    - log.remoteLocation must
       - contain a valid URL
       - specify scheme HTTPS
       - contain userinfo for HTTP Basic Authentication
       - not contain a URL fragment component
       - not contain a URL query components that ends in a slash character ("/")
* Step 4:
    - HTTP status code must be 401 Unauthorized
* Step 6:
    - HTTP status code must be in 2xx-range

Post scenario validations:
    N/a

Remarks
Section heading printed as "TC_N_103_CSMS: Retrieve Log Information - Authentication - HTTPS", while the Test
case Id cell is printed as "TC_N_102_CSMS"; the cell text is transcribed as printed.

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.17. Page 1304-1306 - (2026-02) - TC_N_102_CSMS/TC_N_103_CSMS - added without userinfo
        The first attempt needs to be without to check it is not accepted.

        | Test case Id | TC_N_102_CSMS / TC_N_103_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | 3. The Test System uploads log file to / <GetLogRequest.log.remoteLocation of step 1 without
          userinfo> / using HTTP POST | 4. The CSMS responds using HTTP |
        | … | |
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from diagnostics import upload_log, validate_upload_location
from reusable_states.booted import booted
from trigger import get_log
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_103(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Configuration State: CSMS configured to prevent unauthorised uploading to HTTPS log
    # location.
    # Manual Action: Trigger CSMS to GetLogRequest with logType DiagnosticsLog and remoteLocation
    #                with userinfo for HTTP Basic Authentication
    # 1. CSMS sends a GetLogRequest
    # 2. Test System responds with a GetLogResponse with
    #    - status Accepted
    cp.set_response('GetLog', status='Accepted')
    request = await cp.wait_for_request(
        'GetLog', manual_action=get_log(BASIC_AUTH_CP, 'DiagnosticsLog', scheme='https'))
    assert request.log_type == 'DiagnosticsLog', \
        f"Expected GetLogRequest.logType DiagnosticsLog, got {request.log_type}"
    remote_location = request.log.remote_location
    # log.remoteLocation must contain a valid URL, specify scheme HTTPS, contain userinfo for HTTP
    # Basic Authentication, not contain a URL fragment component, and not contain a URL query
    # component that ends in a slash character ("/")
    validate_upload_location(remote_location, 'https')

    # 3. The Test System uploads log file to <GetLogRequest.log.remoteLocation of step 1 without
    #    userinfo> using HTTP POST (errata 2026-09, 6.3.17)
    # 4. The CSMS responds using HTTP
    status_code = await upload_log(remote_location, with_userinfo=False)
    assert status_code == 401, \
        f"Expected HTTP status code 401 Unauthorized for an upload without userinfo, got {status_code}"

    # 5. The Test System uploads file to <GetLogRequest.log.remoteLocation of step 1> using HTTP
    #    POST
    # 6. The CSMS responds using HTTP
    status_code = await upload_log(remote_location)
    assert 200 <= status_code < 300, \
        f"Expected an HTTP status code in the 2xx-range for the upload, got {status_code}"

    # 7.  Test System sends a LogStatusNotificationRequest with
    #     - status Uploading
    #     - requestId <GetLogRequest.requestId of step 1>
    # 8.  CSMS responds with a LogStatusNotificationResponse
    # 9.  Test System sends a LogStatusNotificationRequest with
    #     - status Uploaded
    #     - requestId <GetLogRequest.requestId of step 1>
    # 10. CSMS responds with a LogStatusNotificationResponse
    for status in ('Uploading', 'Uploaded'):
        await cp.send_log_status_notification_request(status, request_id=request.request_id)

    start_task.cancel()
