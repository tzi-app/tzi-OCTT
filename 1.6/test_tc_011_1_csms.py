"""
Test case name      Remote Start Charging Session – Remote Start First
Test case Id        TC_011_1_CSMS
Chapter             3.4.2 (under 3.4. Core Profile - Remote actions Happy flow)
Protocol            OCPP 1.6J
Document ref        Page 115-116, Table 130
                    (OCPP Compliancy Testing Tool - TestCaseDocument, 2025-11)

System under test   Central System

Description         This scenario is used to start a transaction remotely.

Purpose             To test if the Central System can handle when a Charge point starts a transaction after
                    receiving a RemoteStartTransaction.req from the Central System.

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
    [EV driver plugs in the cable.]
    7.  The Charge Point sends a StartTransaction.req to the Central System.
    8.  The Central System responds with a StartTransaction.conf.
        - idTagInfo.status: Accepted
    9.  The Charge Point sends a StatusNotification.req to the Central System.
        - status: Charging
    10. The Central System responds with a StatusNotification.conf.

Tool validation(s)
    * Step 2:  (Message: RemoteStartTransaction.conf)  status is Accepted
    * Step 4:  (Message: Authorize.conf)  idTagInfo.status is Accepted
    * Step 5:  (Message: StatusNotification.req)  status is Preparing
    * Step 8:  (Message: StartTransaction.conf)  idTagInfo.status is Accepted
    * Step 9:  (Message: StatusNotification.req)  status is Charging

Expected result(s) / behaviour
    n/a

Notes
    - Field-level details in scenario steps (idTag, connectorId, meterStart, etc.) are
      inferred from the OCPP 1.6 specification; the official test case document only lists
      message names without field details (to be verified).
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import AuthorizationStatus, ChargePointStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_011_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send RemoteStartTransaction.req → CP responds Accepted
    await asyncio.wait_for(cp._received_remote_start.wait(), timeout=ACTION_TIMEOUT)
    id_tag = cp._remote_start_id_tag
    assert id_tag is not None

    # Step 3-4: Authorize with the idTag from the remote start
    auth_response = await cp.send_authorize(id_tag)
    assert auth_response.id_tag_info['status'] == AuthorizationStatus.accepted

    # Step 5-6: StatusNotification(Preparing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.preparing)

    # [EV driver plugs in the cable.]

    # Step 7-8: StartTransaction
    start_response = await cp.send_start_transaction(CONNECTOR_ID, id_tag)
    assert start_response.id_tag_info['status'] == AuthorizationStatus.accepted
    assert start_response.transaction_id is not None

    # Step 9-10: StatusNotification(Charging)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.charging)

    start_task.cancel()
