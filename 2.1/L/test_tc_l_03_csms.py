"""
Test case name      Secure Firmware Update - DownloadScheduled
Test case Id        TC_L_03_CSMS
Use case Id(s)      L01
Requirement(s)      L01.FR.01, L01.FR.11, L01.FR.15

Requirement Details:
    L01.FR.01: The Charging Station SHALL send a FirmwareStatusNotificationRequest message to the CSMS with
               this new status. What reason to use is described in the description of FirmwareStatusEnumType.
        Precondition: Whenever the Charging Station enters a new state in the firmware update process.
    L01.FR.11: For security purposes the CSMS SHALL include the Firmware Signing certificate (see Keys used in
               OCPP) in the UpdateFirmwareRequest.
    L01.FR.15: The Charging Station SHALL send a FirmwareStatusNotificationRequest with status
               InstallRebooting, before rebooting.
        Precondition: When a Charging Station needs to reboot before installing the downloaded firmware.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to securely download and install a new
                    firmware by sending an UpdateFirmwareRequest with a signingCertificate.

Purpose             To verify if the CSMS is able to request the Charging Station to schedule securely
                    downloading a new firmware.

Prerequisite(s)     The CSMS configuration firmware retrieveDateTime needs to be set to a future dateTime.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a UpdateFirmwareRequest
2. The Test System responds with a UpdateFirmwareResponse
    - With status Accepted
3. The Test System sends a FirmwareStatusNotificationRequest.
    - With status DownloadScheduled
4. The CSMS responds with a FirmwareStatusNotificationResponse.
5. The Test System sends a FirmwareStatusNotificationRequest.
    - With status Downloading
    Note(s):
    - This step will be executed after the given retrieveDateTime from step 1 has been reached.
6. The CSMS responds with a FirmwareStatusNotificationResponse.
7. The Test System sends a FirmwareStatusNotificationRequest.
    - With status Downloaded
8. The CSMS responds with a FirmwareStatusNotificationResponse.
9. The Test System sends a FirmwareStatusNotificationRequest.
    - With status SignatureVerified
10. The CSMS responds with a FirmwareStatusNotificationResponse.
11. The Test System sends a FirmwareStatusNotificationRequest.
    - With status Installing
12. The CSMS responds with a FirmwareStatusNotificationResponse.
13. The Test System sends a FirmwareStatusNotificationRequest.
    - With status InstallRebooting
14. The CSMS responds with a FirmwareStatusNotificationResponse.
15. The Test System sends a BootNotificationRequest
    - With reason FirmwareUpdate
16. The CSMS responds with a BootNotificationResponse
17. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
18. The CSMS responds accordingly.
19. The Test System sends a FirmwareStatusNotificationRequest.
    - With status Installed
20. The CSMS responds with a FirmwareStatusNotificationResponse.

Tool validations
* Step 1:
    Message UpdateFirmwareRequest
    - firmware.retrieveDateTime <A dateTime in the future>
* Step 16:
    Message BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.15. Page 415 - (2026-04) - L01.FR.04 - removed ECSchnorr algorithm option and clarify the signature
        verification the Charging Station must do
        (Part 2 errata - applies to this test via use case L01)
        |  | ID. | Precondition | Requirements | Note |
        | Old | L01.FR.04 | When the Charging Station has successfully downloaded the new firmware | The
          signature SHALL be validated, by calculating the signature over the entire firmware file using the
          RSA-PSS or ECSchnorr algorithm for signing, and the SHA256 algorithm for calculating hash values. |
          |
        | New | L01.FR.04 | When the Charging Station has successfully downloaded the new firmware | The
          charging station SHALL verify the signature from the UpdateFirmwareRequest with the hash over the
          entire received firmware file computed using the signature hash algorithm. | The RSA-PSS or ECDSA
          algorithm is used for signing. Please refer to section [certificate_properties] for more details
          about signature algorithms and computing hash values. |
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from firmware import (
    reboot_with_new_firmware,
    request_firmware_update,
    SCHEDULE_DELAY,
    seconds_until,
)
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_l_03(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: The CSMS configuration firmware retrieveDateTime needs to be set to a future
    # dateTime.
    # 1. The CSMS sends a UpdateFirmwareRequest
    # 2. The Test System responds with a UpdateFirmwareResponse - With status Accepted
    request = await request_firmware_update(cp, retrieve_in=SCHEDULE_DELAY)
    retrieve_date_time = request.firmware.retrieve_date_time
    assert seconds_until(retrieve_date_time) > 0, \
        f"Expected firmware.retrieveDateTime to be a dateTime in the future, got {retrieve_date_time}"

    # 3. The Test System sends a FirmwareStatusNotificationRequest. - With status
    #    DownloadScheduled
    # 4. The CSMS responds with a FirmwareStatusNotificationResponse.
    await cp.send_firmware_status_notification_request(
        'DownloadScheduled', request_id=request.request_id)

    # 5.  The Test System sends a FirmwareStatusNotificationRequest. - With status Downloading
    #     Note(s): This step will be executed after the given retrieveDateTime from step 1 has
    #     been reached.
    # 6.  The CSMS responds with a FirmwareStatusNotificationResponse.
    # 7.  ... - With status Downloaded
    # 8.  The CSMS responds with a FirmwareStatusNotificationResponse.
    # 9.  ... - With status SignatureVerified
    # 10. The CSMS responds with a FirmwareStatusNotificationResponse.
    # 11. ... - With status Installing
    # 12. The CSMS responds with a FirmwareStatusNotificationResponse.
    # 13. ... - With status InstallRebooting
    # 14. The CSMS responds with a FirmwareStatusNotificationResponse.
    await asyncio.sleep(max(0.0, seconds_until(retrieve_date_time)))
    for status in ('Downloading', 'Downloaded', 'SignatureVerified', 'Installing', 'InstallRebooting'):
        await cp.send_firmware_status_notification_request(status, request_id=request.request_id)

    # 15. The Test System sends a BootNotificationRequest - With reason FirmwareUpdate
    # 16. The CSMS responds with a BootNotificationResponse - status Accepted
    # 17. The Test System notifies the CSMS about the current state of all connectors.
    #     Message: StatusNotificationRequest - connectorStatus Available
    #     Message: NotifyEventRequest - trigger Delta, actualValue "Available", component.name
    #              "Connector", variable.name "AvailabilityState"
    # 18. The CSMS responds accordingly.
    await reboot_with_new_firmware(cp)

    # 19. The Test System sends a FirmwareStatusNotificationRequest. - With status Installed
    # 20. The CSMS responds with a FirmwareStatusNotificationResponse.
    await cp.send_firmware_status_notification_request('Installed', request_id=request.request_id)

    start_task.cancel()
