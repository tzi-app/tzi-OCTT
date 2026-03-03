"""
Test case name      Remote Start Charging Session – Time Out
Test case Id        TC_011_2_CSMS
Chapter             3.4. Core Profile - Remote actions Happy flow
Section             3.4.3. Remote Start Charging Session – Time Out
Protocol            OCPP 1.6J
Doc reference       CompliancyTestTool-TestCaseDocument-CSMS-Section3 (2025-11), Table 131, Page 116-117/176

System under test   Central System

Description         This scenario is used to set a connector back to available, after receiving a
                    RemoteStartTransaction.req and it takes to long to plugin the cable.

Purpose             To test if the Central System can handle when a Charge Point sets the connector back to
                    available, after reaching the configured connection timeout.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
    1.  The Central System sends a RemoteStartTransaction.req to the Charge Point.
    2.  The Charge Point responds with a RemoteStartTransaction.conf.
        - status: Accepted
    3.  The Charge Point sends an Authorize.req to the Central System.
    4.  The Central System responds with an Authorize.conf.
        - idTagInfo.status: Accepted
    5.  The Charge Point sends a StatusNotification.req to the Central System.
        - status: Preparing
    6.  The Central System responds with a StatusNotification.conf.
    [After the configured connection timeout has been reached.]
    7.  The Charge Point sends a StatusNotification.req to the Central System.
        - status: Available
    8.  The Central System responds with a StatusNotification.conf.

Tool validation(s)
    * Step 2:  (Message: RemoteStartTransaction.conf)  status is Accepted
    * Step 4:  (Message: Authorize.conf)  idTagInfo.status is Accepted
    * Step 5:  (Message: StatusNotification.req)  status is Preparing
    * Step 7:  (Message: StatusNotification.req)  status is Available

Expected result(s) / behaviour
    n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import AuthorizationStatus, ChargePointStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers
from trigger import trigger_v16

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
VALID_ID_TAG = os.environ.get('VALID_ID_TOKEN', 'TEST_TAG')


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_011_2(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send RemoteStartTransaction.req → CP responds Accepted
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'remote-start-transaction', {'idTag': VALID_ID_TAG}))
    await asyncio.wait_for(cp._received_remote_start.wait(), timeout=ACTION_TIMEOUT)
    id_tag = cp._remote_start_id_tag
    assert id_tag is not None

    # Step 3-4: Authorize with the idTag from the remote start
    auth_response = await cp.send_authorize(id_tag)
    assert auth_response.id_tag_info['status'] == AuthorizationStatus.accepted

    # Step 5-6: StatusNotification(Preparing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.preparing)

    # [Connection timeout reached — no cable plugged in]

    # Step 7-8: StatusNotification(Available) — connector reverts
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.available)

    start_task.cancel()
