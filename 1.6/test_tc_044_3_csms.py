"""
Test case name      Firmware Update - Installation Failed
Test case Id        TC_044_3_CSMS
Feature profile     FirmwareManagement
Reference           CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf,
                    Section 3.15.3, Table 163, Page 140 (PDF physical page 37)

Description         The firmware of a Charge Point is being updated, but the installation fails.
Purpose             Check whether Central System can handle messages for an update of the firmware of a Charge Point in
                    case the installation fails.

Prerequisite(s)     The Central System supports the Firmware Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1.  The Central System sends a UpdateFirmware.req
    2.  The Charge Point responds with a UpdateFirmware.conf

    [The Charge Point starts downloading the firmware]
    3.  The Charge Point sends a FirmwareStatusNotification.req
    4.  The Central System responds with a FirmwareStatusNotification.conf

    [The Charge Point has finished downloading the firmware]
    5.  The Charge Point sends a FirmwareStatusNotification.req
    6.  The Central System responds with a FirmwareStatusNotification.conf

    [The Charge Point reports the status of all connectors]
    7.  The Charge Point sends a StatusNotification.req
    8.  The Central System responds with a StatusNotification.conf

    [The Charge Point starts installing the firmware]
    9.  The Charge Point sends a FirmwareStatusNotification.req
    10. The Central System responds with a FirmwareStatusNotification.conf

    11. The Charge Point reboots and sends a BootNotification.req
    12. The Central System responds with a BootNotification.conf

    [The Charge Point reports the status of all connectors]
    13. The Charge Point sends a StatusNotification.req
    14. The Central System responds with a StatusNotification.conf

    15. The Charge Point sends a FirmwareStatusNotification.req
    16. The Central System responds with a FirmwareStatusNotification.conf

Tool validations
    Charge Point (Tool):
    * Step 3:
        (Message: FirmwareStatusNotification.req)
        The status is Downloading.

    * Step 5:
        (Message: FirmwareStatusNotification.req)
        The status is Downloaded.

    * Step 7:
        (Message: StatusNotification.req)
        The status is Unavailable.

    * Step 9:
        (Message: FirmwareStatusNotification.req)
        The status is Installing.

    * Step 13:
        (Message: StatusNotification.req)
        The status is Available.

    * Step 15:
        (Message: FirmwareStatusNotification.req)
        The status is InstallationFailed.

    Central System (SUT): n/a

Expected result(s) / behaviour: n/a

Notes:
    - Steps 7-8 and 13-14 say "reports the status of all connectors" but show only a single
      StatusNotification.req/conf pair. Implementation sends one per connector (0 + CONNECTOR_ID).
    - Step 12: Docstring does not specify the expected BootNotification.conf status.
      Implementation asserts Accepted (implied by continued normal operation).
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus, FirmwareStatus, RegistrationStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_044_3(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send UpdateFirmware.req → CP responds with UpdateFirmware.conf
    await asyncio.wait_for(cp._received_update_firmware.wait(), timeout=ACTION_TIMEOUT)
    assert cp._update_firmware_data is not None

    # Step 3-4: CP sends FirmwareStatusNotification(Downloading)
    await cp.send_firmware_status_notification(FirmwareStatus.downloading)

    # Step 5-6: CP sends FirmwareStatusNotification(Downloaded)
    await cp.send_firmware_status_notification(FirmwareStatus.downloaded)

    # Step 7-8: CP reports StatusNotification(Unavailable) for all connectors
    for cid in (0, CONNECTOR_ID):
        await cp.send_status_notification(cid, status=ChargePointStatus.unavailable)

    # Step 9-10: CP sends FirmwareStatusNotification(Installing)
    await cp.send_firmware_status_notification(FirmwareStatus.installing)

    # Step 11-12: CP reboots and sends BootNotification
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 13-14: CP reports StatusNotification(Available) for all connectors
    for cid in (0, CONNECTOR_ID):
        await cp.send_status_notification(cid, status=ChargePointStatus.available)

    # Step 15-16: CP sends FirmwareStatusNotification(InstallationFailed)
    await cp.send_firmware_status_notification(FirmwareStatus.installation_failed)

    start_task.cancel()
