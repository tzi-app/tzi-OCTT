"""
Test case name      Secure Firmware Update
Test case Id        TC_080_CSMS
Section             3.21.3 Secure firmware update
System under test   Central System
Document reference  Table 192, pages 164-166 (CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, 2025-11)

Description         The firmware of a Charge Point is updated in a secure way.

Purpose             To check whether Central System can trigger a Charge Point to update its firmware in a secure way.

Prerequisite(s)     - The Central System supports the Firmware Management feature profile AND
                    - The Central System supports a security profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a SignedUpdateFirmware.req
    2. The Charge Point sends a SignedUpdateFirmware.conf

    3. The Charge Point sends a SignedFirmwareStatusNotification.req (status: Downloading)
    4. The Central System responds with a SignedFirmwareStatusNotification.conf

    [The Charge Point has finished downloading the firmware]
    5. The Charge Point sends a SignedFirmwareStatusNotification.req (status: Downloaded)
    6. The Central System responds with a SignedFirmwareStatusNotification.conf

    [The Charge Point has verified the signature]
    7. The Charge Point sends a SignedFirmwareStatusNotification.req (status: SignatureVerified)
    8. The Central System responds with a SignedFirmwareStatusNotification.conf

    [Before installing firmware the Charge Point MAY set all connectors to Unavailable.
     If the Charge Point supports installation of firmware during a charging session,
     the Charge Point MAY install the firmware after only setting all other connectors to Unavailable.]

    [The Charge Point starts installing the firmware]
    9. The Charge Point sends a SignedFirmwareStatusNotification.req (status: Installing)
    10. The Central System responds with a SignedFirmwareStatusNotification.conf

    11. The Charge Point sends a SignedFirmwareStatusNotification.req (status: InstallRebooting)
    12. The Central System responds with a SignedFirmwareStatusNotification.conf

    13. The Charge Point sends a BootNotification.req
    14. The Central System responds with a BootNotification.conf

    15. The Charge Point sends a SecurityEventNotification.req (type: FirmwareUpdated)
    16. The Central System responds with a SecurityEventNotification.conf

    17. The Charge Point sends a StatusNotification.req (status: Available)
    18. The Central System responds with a StatusNotification.conf

    [The Charge Point has finished installing the firmware]
    19. The Charge Point sends a SignedFirmwareStatusNotification.req (status: Installed)
    20. The Central System responds with a SignedFirmwareStatusNotification.conf

Tool Validations
    * Step 1:
        (Message: SignedUpdateFirmware.req)
        firmware.location is <Configured Firmware Download URL>
        firmware.signature is <Configured signature>
        firmware.signingCertificate is <Configured signingCertificate>
        After step 2 and before step 9:
        the CS responds to the StatusNotification.req with a StatusNotification.conf

    * Step 3:
        (Message: SignedFirmwareStatusNotification.req)
        The status is Downloading

    * After step 2 and before step 9:
        Message: StatusNotification.req
        The status is Unavailable

    * Step 5:
        (Message: SignedFirmwareStatusNotification.req)
        The status is Downloaded

    * Step 7:
        (Message: SignedFirmwareStatusNotification.req)
        The status is SignatureVerified

    * Step 9:
        (Message: SignedFirmwareStatusNotification.req)
        The status is Installing

    * Step 11:
        (Message: SignedFirmwareStatusNotification.req)
        The status is InstallRebooting

    * Step 15:
        (Message: SecurityEventNotification.req)
        type FirmwareUpdated

    * Step 17:
        (Message: StatusNotification.req)
        The status is Available

    * Step 19:
        (Message: SignedFirmwareStatusNotification.req)
        The status is Installed

    * Step 13 / 15 / 17 / 19:
        The messages can be in a different order.

Expected result(s) / behaviour:
    Charge Point: The Charge Point handles the firmware update correctly and is Available after the update.
    Central System: The Central System receives and responds to the FirmwareStatusNotification messages.
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


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_080(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send SignedUpdateFirmware.req
    await asyncio.wait_for(cp._received_signed_update_firmware.wait(), timeout=ACTION_TIMEOUT)
    assert cp._signed_update_firmware_data is not None
    request_id = cp._signed_update_firmware_data['request_id']

    # Step 3-4: SignedFirmwareStatusNotification (Downloading)
    await cp.send_signed_firmware_status_notification(
        status=FirmwareStatus.downloading,
        request_id=request_id,
    )

    # Step 5-6: SignedFirmwareStatusNotification (Downloaded)
    await cp.send_signed_firmware_status_notification(
        status=FirmwareStatus.downloaded,
        request_id=request_id,
    )

    # Step 7-8: SignedFirmwareStatusNotification (SignatureVerified)
    await cp.send_signed_firmware_status_notification(
        status=FirmwareStatus.signature_verified,
        request_id=request_id,
    )

    # Before installing: set connectors to Unavailable
    for cid in (0, 1):
        await cp.send_status_notification(cid, status=ChargePointStatus.unavailable)

    # Step 9-10: SignedFirmwareStatusNotification (Installing)
    await cp.send_signed_firmware_status_notification(
        status=FirmwareStatus.installing,
        request_id=request_id,
    )

    # Step 11-12: SignedFirmwareStatusNotification (InstallRebooting)
    await cp.send_signed_firmware_status_notification(
        status=FirmwareStatus.install_rebooting,
        request_id=request_id,
    )

    # Step 13-14: BootNotification after reboot
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 15-16: SecurityEventNotification (FirmwareUpdated)
    await cp.send_security_event_notification('FirmwareUpdated')

    # Step 17-18: StatusNotification (Available) for connectors
    for cid in (0, 1):
        await cp.send_status_notification(cid, status=ChargePointStatus.available)

    # Step 19-20: SignedFirmwareStatusNotification (Installed)
    await cp.send_signed_firmware_status_notification(
        status=FirmwareStatus.installed,
        request_id=request_id,
    )

    start_task.cancel()
