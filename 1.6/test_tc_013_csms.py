"""
Test case name      Hard Reset
Test case Id        TC_013_CSMS
Table               133
Document ref        Page 119 of 176 (CompliancyTestTool-TestCaseDocument, 2025-11)
Section             3.5.1 - Core Profile - Resetting Happy Flow
System under test   Central System (SUT)

Description         This scenario is used to hard reset a Charge Point.
Purpose             To test if the Central System is able to trigger a hard reset.

Prerequisite(s)     n/a
Before
    Configuration State(s):  n/a
    Memory State(s):         n/a
    Reusable State(s):       n/a

Scenario Detail(s)
    Charge Point (Tool)                          Central System (SUT)
    2. CP responds with Reset.conf               1. CS sends a Reset.req
    3. CP sends a BootNotification.req           4. CS responds with BootNotification.conf
    [Send per connector and connectorId=0.]      6. CS responds with StatusNotification.conf
    5. CP sends a StatusNotification.req

    Note: The number of connectors is not specified. Implementation assumes 1 connector
    (connectorId=1) plus connectorId=0 for the charge point itself.

Tool validation(s)
    Charge Point (Tool):
    - Step 2: (Message: Reset.conf) status is Accepted
    - Step 5: (Message: StatusNotification.req) status is Available
    Central System (SUT):
    - Step 1: (Message: Reset.req) type is Hard
    - Step 4: (Message: BootNotification.conf) status is Accepted

Expected result(s) / behaviour    n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus, RegistrationStatus, ResetType

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers
from trigger import trigger_v16

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_013(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send Reset.req (type=Hard) → CP responds Accepted
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'reset', {'type': 'Hard'}))
    await asyncio.wait_for(cp._received_reset.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reset_type == ResetType.hard

    # Step 3-4: CP reboots → sends BootNotification
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 5-6: Send StatusNotification(Available) per connector and connectorId=0
    for connector_id in (0, 1):
        await cp.send_status_notification(connector_id, status=ChargePointStatus.available)

    start_task.cancel()
