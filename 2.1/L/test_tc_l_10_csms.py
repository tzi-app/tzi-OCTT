"""
Test case name      Secure Firmware Update - AcceptedCanceled
Test case Id        TC_L_10_CSMS
Use case Id(s)      L01
Requirement(s)      L01.FR.01, L01.FR.11, L01.FR.24

Requirement Details:
    L01.FR.01: The Charging Station SHALL send a FirmwareStatusNotificationRequest message to the CSMS with
               this new status. What reason to use is described in the description of FirmwareStatusEnumType.
        Precondition: Whenever the Charging Station enters a new state in the firmware update process.
    L01.FR.11: For security purposes the CSMS SHALL include the Firmware Signing certificate (see Keys used in
               OCPP) in the UpdateFirmwareRequest.
    L01.FR.24: The Charging Station SHOULD cancel the ongoing firmware update AND respond with status
               AcceptedCanceled.
        Precondition: When a Charging Station is installing new Firmware OR is going to install new Firmware,
                      but has received an UpdateFirmware command to install it at a later time AND the
                      Charging Station receives a new UpdateFirmwareRequest
        Note: The Charging Station SHOULD NOT first check if the new firmware file exists, this way the CSMS
              will be able to cancel an ongoing firmware update without starting a new one. The Charging
              Station may send a FirmwareStatusNotificationRequest with status DownloadFailed or
              InstallationFailed for the firmware update that has now been canceled.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to securely download and install a new
                    firmware by sending an UpdateFirmwareRequest with a signingCertificate.

Purpose             To verify if the CSMS is able to handle a Charging Station reporting an ongoing
                    installation of a firmware was canceled and it is now starting the new firmware update.

Prerequisite(s)     The CSMS is able to request a new firmware update, while there is already one ongoing on
                    the Charging Station.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a UpdateFirmwareRequest
2. The Test System responds with a UpdateFirmwareResponse
    With status Accepted
3. The Test System sends a FirmwareStatusNotificationRequest.
    With status Downloading
4. The CSMS responds with a FirmwareStatusNotificationResponse.
5. The CSMS sends a UpdateFirmwareRequest
6. The Test System responds with a UpdateFirmwareResponse
    With status AcceptedCanceled
7. The Test System sends a FirmwareStatusNotificationRequest.
    With status Downloading
8. The CSMS responds with a FirmwareStatusNotificationResponse.
9. The Test System sends a FirmwareStatusNotificationRequest.
    With status Downloaded
10. The CSMS responds with a FirmwareStatusNotificationResponse.
11. The Test System sends a FirmwareStatusNotificationRequest.
    With status SignatureVerified
12. The CSMS responds with a FirmwareStatusNotificationResponse.
13. The Test System sends a FirmwareStatusNotificationRequest.
    With status Installing
14. The CSMS responds with a FirmwareStatusNotificationResponse.
15. The Test System sends a FirmwareStatusNotificationRequest.
    With status InstallRebooting
16. The CSMS responds with a FirmwareStatusNotificationResponse.
17. The Test System sends a BootNotificationRequest
    With reason FirmwareUpdate
18. The CSMS responds with a BootNotificationResponse
19. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
20. The CSMS responds accordingly.
21. The Test System sends a FirmwareStatusNotificationRequest.
    With status Installed
22. The CSMS responds with a FirmwareStatusNotificationResponse.

Tool validations
* Step 18:
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
from firmware import reboot_with_new_firmware, request_firmware_update
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_l_10(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: The CSMS is able to request a new firmware update, while there is already one
    # ongoing on the Charging Station.
    # 1. The CSMS sends a UpdateFirmwareRequest
    # 2. The Test System responds with a UpdateFirmwareResponse With status Accepted
    first = await request_firmware_update(cp, request_id=1)

    # 3. The Test System sends a FirmwareStatusNotificationRequest. With status Downloading
    # 4. The CSMS responds with a FirmwareStatusNotificationResponse.
    await cp.send_firmware_status_notification_request('Downloading', request_id=first.request_id)

    # 5. The CSMS sends a UpdateFirmwareRequest
    # 6. The Test System responds with a UpdateFirmwareResponse With status AcceptedCanceled
    second = await request_firmware_update(cp, status='AcceptedCanceled', request_id=2)

    # The ongoing firmware update is canceled, and the Test System does the new one.
    # 7.  The Test System sends a FirmwareStatusNotificationRequest. With status Downloading
    # 8.  The CSMS responds with a FirmwareStatusNotificationResponse.
    # 9.  ... With status Downloaded
    # 10. The CSMS responds with a FirmwareStatusNotificationResponse.
    # 11. ... With status SignatureVerified
    # 12. The CSMS responds with a FirmwareStatusNotificationResponse.
    # 13. ... With status Installing
    # 14. The CSMS responds with a FirmwareStatusNotificationResponse.
    # 15. ... With status InstallRebooting
    # 16. The CSMS responds with a FirmwareStatusNotificationResponse.
    for status in ('Downloading', 'Downloaded', 'SignatureVerified', 'Installing', 'InstallRebooting'):
        await cp.send_firmware_status_notification_request(status, request_id=second.request_id)

    # 17. The Test System sends a BootNotificationRequest With reason FirmwareUpdate
    # 18. The CSMS responds with a BootNotificationResponse - status Accepted
    # 19. The Test System notifies the CSMS about the current state of all connectors.
    #     Message: StatusNotificationRequest - connectorStatus Available
    #     Message: NotifyEventRequest - trigger Delta, actualValue "Available", component.name
    #              "Connector", variable.name "AvailabilityState"
    # 20. The CSMS responds accordingly.
    await reboot_with_new_firmware(cp)

    # 21. The Test System sends a FirmwareStatusNotificationRequest. With status Installed
    # 22. The CSMS responds with a FirmwareStatusNotificationResponse.
    await cp.send_firmware_status_notification_request('Installed', request_id=second.request_id)

    start_task.cancel()
