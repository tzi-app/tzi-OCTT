"""
Test case name      Firmware Update - Download and Install
Test case Id        TC_044_1_CSMS
Feature profile     FirmwareManagement
Document ref        Section 3.15.1, Table 161, p. 138 (CompliancyTestTool-TestCaseDocument, 2025-11)

Description         The firmware of a Charge Point is updated.
Purpose             Check whether Central System can trigger an update of the firmware of a Charge Point.

Prerequisite(s)     The Central System supports the Firmware Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    Charge Point (Tool)                             Central System (SUT)
    -----------------------------------------------------------------------
    2.  The Charge Point responds with a            1.  The Central System sends a
        UpdateFirmware.conf                             UpdateFirmware.req

    [The Charge Point starts downloading the firmware]
    3.  The Charge Point sends a                    4.  The Central System responds with a
        FirmwareStatusNotification.req                  FirmwareStatusNotification.conf

    [The Charge Point has finished downloading the firmware]
    5.  The Charge Point sends a                    6.  The Central System responds with a
        FirmwareStatusNotification.req                  FirmwareStatusNotification.conf

    [The Charge Point reports the status of all connectors]
    7.  The Charge Point sends a                    8.  The Central System responds with a
        StatusNotification.req                          StatusNotification.conf

    [The Charge Point starts installing the firmware]
    9.  The Charge Point sends a                    10. The Central System responds with a
        FirmwareStatusNotification.req                  FirmwareStatusNotification.conf

    11. The Charge Point sends a                    12. The Central System responds with a
        BootNotification.req                            BootNotification.conf

    [The Charge Point reports the status of all connectors]
    13. The Charge Point sends a                    14. The Central System responds with a
        StatusNotification.req                          StatusNotification.conf

    15. The Charge Point sends a                    16. The Central System responds with a
        FirmwareStatusNotification.req                  FirmwareStatusNotification.conf

Tool validations
    * Step 1 (Central System):
        (Message: UpdateFirmware.req)
        The firmware.location is <Firmware Download URL from test data>.

    * Step 3 (Charge Point):
        (Message: FirmwareStatusNotification.req)
        The status is Downloading.

    * Step 5 (Charge Point):
        (Message: FirmwareStatusNotification.req)
        The status is Downloaded.

    * Step 7 (Charge Point):
        (Message: StatusNotification.req)
        The status is Unavailable.

    * Step 9 (Charge Point):
        (Message: FirmwareStatusNotification.req)
        The status is Installing.

    * Step 13 (Charge Point):
        (Message: StatusNotification.req)
        The status is Available.

    * Step 15 (Charge Point):
        (Message: FirmwareStatusNotification.req)
        The status is Installed.

Expected result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus, FirmwareStatus, RegistrationStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_044_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send UpdateFirmware.req → CP responds with UpdateFirmware.conf
    await asyncio.wait_for(cp._received_update_firmware.wait(), timeout=ACTION_TIMEOUT)
    assert cp._update_firmware_data is not None

    # Step 3-4: FirmwareStatusNotification(Downloading)
    await cp.send_firmware_status_notification(FirmwareStatus.downloading)

    # Step 5-6: FirmwareStatusNotification(Downloaded)
    await cp.send_firmware_status_notification(FirmwareStatus.downloaded)

    # Step 7-8: StatusNotification(Unavailable) for each connector
    for cid in (0, CONNECTOR_ID):
        await cp.send_status_notification(cid, status=ChargePointStatus.unavailable)

    # Step 9-10: FirmwareStatusNotification(Installing)
    await cp.send_firmware_status_notification(FirmwareStatus.installing)

    # Step 11-12: BootNotification after firmware install
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 13-14: StatusNotification(Available) for each connector
    for cid in (0, CONNECTOR_ID):
        await cp.send_status_notification(cid, status=ChargePointStatus.available)

    # Step 15-16: FirmwareStatusNotification(Installed)
    await cp.send_firmware_status_notification(FirmwareStatus.installed)

    start_task.cancel()
