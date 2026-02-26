"""
Test case name      Firmware Update - Download Failed
Test case Id        TC_044_2_CSMS
Feature profile     FirmwareManagement
Reference           CompliancyTestTool-TestCaseDocument, Section 3.15.2, Table 162, Page 139/176

Description         The firmware of a Charge Point is being updated, but downloading the firmware fails.
Purpose             Check whether Central System can handle messages for a firmware update in case downloading of the
                    firmware fails.

Prerequisite(s)     The Central System supports the Firmware Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1.  The Central System sends a UpdateFirmware.req
        - location: <Firmware Download URL from test data>
    2.  The Charge Point responds with a UpdateFirmware.conf

    [The Charge Point starts downloading the firmware]
    3.  The Charge Point sends a FirmwareStatusNotification.req
        - status: Downloading
    4.  The Central System responds with a FirmwareStatusNotification.conf

    [Downloading the firmware fails]
    5.  The Charge Point sends a FirmwareStatusNotification.req
        - status: DownloadFailed
    6.  The Central System responds with a FirmwareStatusNotification.conf

Tool validations
    * Step 3 (Charge Point):
        (Message: FirmwareStatusNotification.req)
        The status is Downloading.

    * Step 5 (Charge Point):
        (Message: FirmwareStatusNotification.req)
        The status is DownloadFailed.

Expected result(s) / behaviour
    n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import FirmwareStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_044_2(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send UpdateFirmware.req → CP responds with UpdateFirmware.conf
    await asyncio.wait_for(cp._received_update_firmware.wait(), timeout=ACTION_TIMEOUT)
    assert cp._update_firmware_data is not None

    # Step 3-4: CP sends FirmwareStatusNotification(Downloading)
    await cp.send_firmware_status_notification(FirmwareStatus.downloading)

    # Step 5-6: CP sends FirmwareStatusNotification(DownloadFailed)
    await cp.send_firmware_status_notification(FirmwareStatus.download_failed)

    start_task.cancel()
