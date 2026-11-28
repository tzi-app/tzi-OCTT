"""
Test case name      Publish Firmware - Published
Test case Id        TC_L_17_CSMS
Use case Id(s)      L03
Requirement(s)      N/a
System under test   CSMS

Description         The Local Controller downloads and publishes a firmware update at the specified URL. This
                    allows the CSMS to send UpdateFirmwareRequests with the URI pointing to the Local
                    Controller, to any Charging Station connected to the Local Controller. This allows the
                    site to save bandwidth and data on the WAN interface.

Purpose             To verify if the CSMS is able to publish a firmware on the local controller as described
                    at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a PublishFirmwareRequest
2. The Test System responds with a PublishFirmwareResponse with
    - status Accepted
3. The Test System sends a PublishFirmwareStatusNotificationRequest with
    - status Downloading
4. The CSMS responds with a PublishFirmwareStatusNotificationResponse
5. The Test System sends a PublishFirmwareStatusNotificationRequest with
    - status Downloaded
6. The CSMS responds with a PublishFirmwareStatusNotificationResponse
7. The Test System sends a PublishFirmwareStatusNotificationRequest with
    - status ChecksumVerified
8. The CSMS responds with a PublishFirmwareStatusNotificationResponse
9. The Test System sends a PublishFirmwareStatusNotificationRequest with
    - status Published AND
    - location <Configured firmware_location>
10. The CSMS responds with a PublishFirmwareStatusNotificationResponse

Tool validations
* Step 1:
    Message PublishFirmwareRequest
    - location <Configured firmware_location>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from firmware import FIRMWARE_LOCATION, request_publish_firmware
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_l_17(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a PublishFirmwareRequest - location <Configured firmware_location>
    # 2. The Test System responds with a PublishFirmwareResponse with
    #    - status Accepted
    request = await request_publish_firmware(cp)

    # 3. The Test System sends a PublishFirmwareStatusNotificationRequest with
    #    - status Downloading
    # 4. The CSMS responds with a PublishFirmwareStatusNotificationResponse
    # 5. ... with - status Downloaded
    # 6. The CSMS responds with a PublishFirmwareStatusNotificationResponse
    # 7. ... with - status ChecksumVerified
    # 8. The CSMS responds with a PublishFirmwareStatusNotificationResponse
    for status in ('Downloading', 'Downloaded', 'ChecksumVerified'):
        await cp.send_publish_firmware_status_notification_request(
            status, request_id=request.request_id)

    # 9.  The Test System sends a PublishFirmwareStatusNotificationRequest with
    #     - status Published AND
    #     - location <Configured firmware_location>
    # 10. The CSMS responds with a PublishFirmwareStatusNotificationResponse
    await cp.send_publish_firmware_status_notification_request(
        'Published', location=[FIRMWARE_LOCATION], request_id=request.request_id)

    start_task.cancel()
