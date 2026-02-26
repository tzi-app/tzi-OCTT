"""
Test case name      Get Diagnostics
Test case Id        TC_045_1_CSMS
Section             3.16.1 (OCPP 1.6J Diagnostics)
System under test   Central System
Reference           Table 164, page 141/176 of CompliancyTestTool-TestCaseDocument

Description         The Charge Point uploads a diagnostics log to a specified location based on a request of the
                    Central System.

Purpose             The purpose of this test case is to check whether Central System can trigger the Charge Point
                    to upload its diagnostics.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System sends a GetDiagnostics.req to the Charge Point.
   Required fields:
       - location (string): URI where the diagnostics file shall be uploaded to.
   Optional fields:
       - retries (integer): Number of times the Charge Point should retry uploading.
       - retryInterval (integer): Interval in seconds between upload retry attempts.
       - startTime (dateTime): Date and time of the oldest logging information to include.
       - stopTime (dateTime): Date and time of the latest logging information to include.

2. The Charge Point responds with a GetDiagnostics.conf to the Central System.
   Optional fields:
       - fileName (string): Name of the file with diagnostics information that will be uploaded.
         Absence indicates no diagnostics file is available.

   [The Charge Point starts uploading the diagnostics log.]

3. The Charge Point sends a DiagnosticsStatusNotification.req to the Central System.
   Required fields:
       - status (DiagnosticsStatus): "Uploading"
   DiagnosticsStatus enum values: Idle | Uploaded | UploadFailed | Uploading

4. The Central System responds with a DiagnosticsStatusNotification.conf to the Charge Point.
   Response body is empty (no fields).

   [The Charge Point has finished uploading the diagnostics log.]

5. The Charge Point sends a DiagnosticsStatusNotification.req to the Central System.
   Required fields:
       - status (DiagnosticsStatus): "Uploaded"

6. The Central System responds with a DiagnosticsStatusNotification.conf to the Charge Point.
   Response body is empty (no fields).

Tool validations (Charge Point / OCTT side)
* Step 3:
    Message: DiagnosticsStatusNotification.req
    - status is "Uploading"
* Step 5:
    Message: DiagnosticsStatusNotification.req
    - status is "Uploaded"

Expected result(s) / behaviour
    Charge Point (Tool):    The Charge Point has uploaded the diagnostics log to the location
                            that was sent in step 1.
    Central System (SUT):   n/a

OCPP 1.6 Protocol Notes
- Action names: GetDiagnostics, DiagnosticsStatusNotification
- GetDiagnostics is initiated by the Central System (CS -> CP).
- DiagnosticsStatusNotification is initiated by the Charge Point (CP -> CS).
- The Central System must handle the DiagnosticsStatusNotification.req by responding with
  an empty DiagnosticsStatusNotification.conf.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import DiagnosticsStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_045_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send GetDiagnostics.req → CP responds with GetDiagnostics.conf
    await asyncio.wait_for(cp._received_get_diagnostics.wait(), timeout=ACTION_TIMEOUT)
    assert cp._get_diagnostics_data is not None

    # Step 3-4: CP sends DiagnosticsStatusNotification(Uploading)
    await cp.send_diagnostics_status_notification(DiagnosticsStatus.uploading)

    # Step 5-6: CP sends DiagnosticsStatusNotification(Uploaded)
    await cp.send_diagnostics_status_notification(DiagnosticsStatus.uploaded)

    start_task.cancel()
