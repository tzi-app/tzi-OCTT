"""
Test case name      Soft Reset
Test case Id        TC_014_CSMS
Profile             Core
Section             3.5. Core Profile - Resetting Happy Flow / 3.5.2. Soft Reset
Protocol            OCPP 1.6J
Document reference  Table 134, Page 119/176

System under test   Central System (CSMS)

Description         This scenario is used to soft reset a Charge Point.
Purpose             To test if the Central System is able to trigger a soft reset.

Prerequisite(s)     n/a

Test Scenario
1. The Central System sends a Reset.req to the Charge Point with type = "Soft".
2. The Charge Point responds with a Reset.conf with status = "Accepted".
3. The Charge Point sends a BootNotification.req (simulating reboot after soft reset).
4. The Central System responds with a BootNotification.conf with status = "Accepted".
5. The Charge Point sends a StatusNotification.req for each connector (including connectorId=0)
   with status = "Available".
6. The Central System responds with a StatusNotification.conf for each StatusNotification.req.

Validations
- Step 1: Reset.req field "type" must be "Soft".
- Step 2: Reset.conf field "status" must be "Accepted".
- Step 4: BootNotification.conf field "status" must be "Accepted".
- Step 5: StatusNotification.req field "status" must be "Available".
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus, RegistrationStatus, ResetType

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_014(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send Reset.req (type=Soft) → CP responds Accepted
    await asyncio.wait_for(cp._received_reset.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reset_type == ResetType.soft

    # Step 3-4: CP reboots → sends BootNotification
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 5-6: Send StatusNotification(Available) per connector and connectorId=0
    for connector_id in (0, 1):
        await cp.send_status_notification(connector_id, status=ChargePointStatus.available)

    start_task.cancel()
