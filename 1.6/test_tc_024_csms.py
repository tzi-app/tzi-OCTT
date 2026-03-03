"""
Test case name      Start Charging Session Lock Failure
Test case Id        TC_024_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.8.4 - Core Profile - Basic Actions Non-happy flow
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, Table 144, Page 127/176

Description         This scenario is used to report a connector lock failure.

Purpose             To test if the Central System is able to handle a report of a connector lock failure.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): Authorized

Test Scenario
    1. The Charge Point sends a StatusNotification.req
    2. The Central System responds with a StatusNotification.conf
    [EV driver plugs in the cable.]
    3. The Charge Point sends a StatusNotification.req
    4. The Central System responds with a StatusNotification.conf

Tool Validations
    * Step 1 (StatusNotification.req): status is Preparing
    * Step 3 (StatusNotification.req): errorCode is ConnectorLockFailure, status is Faulted

Expected Result     n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointErrorCode, ChargePointStatus

from charge_point import TziChargePoint16
from reusable_states import authorized
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_024(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: Reusable State Authorized
    await authorized(cp, VALID_ID_TAG)

    # Step 1-2: StatusNotification(Preparing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.preparing)

    # Step 3-4: StatusNotification(Faulted, ConnectorLockFailure)
    await cp.send_status_notification(
        CONNECTOR_ID,
        status=ChargePointStatus.faulted,
        error_code=ChargePointErrorCode.connector_lock_failure,
    )

    start_task.cancel()
