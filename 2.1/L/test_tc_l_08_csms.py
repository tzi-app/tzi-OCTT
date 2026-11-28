"""
Test case name      Secure Firmware Update - InstallVerificationFailed
Test case Id        TC_L_08_CSMS
Use case Id(s)      L01
Requirement(s)      L01.FR.01, L01.FR.11

Requirement Details:
    L01.FR.01: The Charging Station SHALL send a FirmwareStatusNotificationRequest message to the CSMS with
               this new status. What reason to use is described in the description of FirmwareStatusEnumType.
        Precondition: Whenever the Charging Station enters a new state in the firmware update process.
    L01.FR.11: For security purposes the CSMS SHALL include the Firmware Signing certificate (see Keys used in
               OCPP) in the UpdateFirmwareRequest.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to securely download and install a new
                    firmware by sending an UpdateFirmwareRequest with a signingCertificate.

Purpose             To verify if the CSMS is able to handle a Charging Station reporting the verification of
                    the firmware failed during installation.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a UpdateFirmwareRequest
2. The Test System responds with a UpdateFirmwareResponse
    - With status Accepted
3. The Test System sends a FirmwareStatusNotificationRequest.
    - With status Downloading
4. The CSMS responds with a FirmwareStatusNotificationResponse.
5. The Test System sends a FirmwareStatusNotificationRequest.
    - With status Downloaded
6. The CSMS responds with a FirmwareStatusNotificationResponse.
7. The Test System sends a FirmwareStatusNotificationRequest.
    - With status SignatureVerified
8. The CSMS responds with a FirmwareStatusNotificationResponse.
9. The Test System sends a FirmwareStatusNotificationRequest.
    - With status Installing
10. The CSMS responds with a FirmwareStatusNotificationResponse.
11. The Test System sends a FirmwareStatusNotificationRequest.
    - With status InstallVerificationFailed
12. The CSMS responds with a FirmwareStatusNotificationResponse.

Tool validations
N/a

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
from firmware import request_firmware_update
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_l_08(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a UpdateFirmwareRequest
    # 2. The Test System responds with a UpdateFirmwareResponse - With status Accepted
    request = await request_firmware_update(cp)

    # 3.  The Test System sends a FirmwareStatusNotificationRequest. - With status Downloading
    # 4.  The CSMS responds with a FirmwareStatusNotificationResponse.
    # 5.  ... - With status Downloaded
    # 6.  The CSMS responds with a FirmwareStatusNotificationResponse.
    # 7.  ... - With status SignatureVerified
    # 8.  The CSMS responds with a FirmwareStatusNotificationResponse.
    # 9.  ... - With status Installing
    # 10. The CSMS responds with a FirmwareStatusNotificationResponse.
    # 11. ... - With status InstallVerificationFailed
    # 12. The CSMS responds with a FirmwareStatusNotificationResponse.
    for status in ('Downloading', 'Downloaded', 'SignatureVerified', 'Installing',
                   'InstallVerificationFailed'):
        await cp.send_firmware_status_notification_request(status, request_id=request.request_id)

    start_task.cancel()
