"""
Test case name      Remote Start Charging Session – Cable Plugged in First
Test case Id        TC_010_CSMS
Table               129
Page                115/176
Chapter             3.4. Core Profile - Remote actions Happy flow
Section             3.4.1. Remote Start Charging Session – Cable Plugged in First
Protocol            OCPP 1.6J

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
    [EV driver plugs in the cable.]
    1.  The Charge Point sends a StatusNotification.req
    2.  The Central System responds with a StatusNotification.conf
    3.  The Central System sends a RemoteStartTransaction.req
    4.  The Charge Point responds with a RemoteStartTransaction.conf
    5.  The Charge Point sends an Authorize.req
    6.  The Central System responds with an Authorize.conf
    7.  The Charge Point sends a StartTransaction.req
    8.  The Central System responds with a StartTransaction.conf
    9.  The Charge Point sends a StatusNotification.req
    10. The Central System responds with a StatusNotification.conf

Tool validation(s)
    * Step 1:  (Message: StatusNotification.req)  status is Preparing
    * Step 4:  (Message: RemoteStartTransaction.conf)  status is Accepted
    * Step 6:  (Message: Authorize.conf)  idTagInfo.status is Accepted
    * Step 8:  (Message: StartTransaction.conf)  idTagInfo.status is Accepted
    * Step 9:  (Message: StatusNotification.req)  status is Charging

Expected result(s) / behaviour
    n/a

Notes (to be fixed later)
    - The official doc scenario only lists message names per step. Field-level details
      (connectorId, errorCode, idTag, meterStart, timestamp, transactionId, etc.) need
      to be inferred from the OCPP 1.6 specification and verified against actual OCTT behavior.
    - The official doc does not specify which idTag value should be used in step 3
      (RemoteStartTransaction.req) or whether connectorId is required/optional.
    - The official doc does not specify the exact fields expected in StartTransaction.req (step 7).
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
async def test_tc_010(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: EV driver plugs in cable → StatusNotification(Preparing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.preparing)

    # Step 3-4: Wait for CSMS to send RemoteStartTransaction.req → CP responds Accepted
    await asyncio.wait_for(cp._received_remote_start.wait(), timeout=ACTION_TIMEOUT)
    id_tag = cp._remote_start_id_tag
    assert id_tag is not None

    # Step 5-6: Authorize with the idTag from the remote start
    auth_response = await cp.send_authorize(id_tag)
    assert auth_response.id_tag_info['status'] == AuthorizationStatus.accepted

    # Step 7-8: StartTransaction
    start_response = await cp.send_start_transaction(CONNECTOR_ID, id_tag)
    assert start_response.id_tag_info['status'] == AuthorizationStatus.accepted
    assert start_response.transaction_id is not None

    # Step 9-10: StatusNotification(Charging)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.charging)

    start_task.cancel()
