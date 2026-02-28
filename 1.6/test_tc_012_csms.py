"""
Test case name      Remote Stop Charging Session
Test case Id        TC_012_CSMS
Chapter             3.4.4 (under 3.4. Core Profile - Remote actions Happy flow)
Protocol            OCPP 1.6J
Document ref        Page 117-118, Table 132
                    (OCPP Compliancy Testing Tool - TestCaseDocument - CSMS - Section 3, 2025-11)

System under test   Central System

Description         This scenario is used to remotely stop a transaction.

Purpose             To test if the Central System can remotely stop a transaction.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      Charging (Table 201 - simulates CP starting a transaction;
                            itself requires Reusable State: Authorized)

Test Scenario
    1.  The Central System sends a RemoteStopTransaction.req to the Charge Point.
    2.  The Charge Point responds with a RemoteStopTransaction.conf.
    3.  The Charge Point sends a StopTransaction.req to the Central System.
    4.  The Central System responds with a StopTransaction.conf.
    5.  The Charge Point sends a StatusNotification.req to the Central System.
    6.  The Central System responds with a StatusNotification.conf.
    [EV driver unplugs the cable.]
    7.  The Charge Point sends a StatusNotification.req to the Central System.
    8.  The Central System responds with a StatusNotification.conf.

Tool validation(s)
    * Step 2:  (Message: RemoteStopTransaction.conf)  status is Accepted
    * Step 3:  (Message: StopTransaction.req)  reason is Remote
    * Step 5:  (Message: StatusNotification.req)  status is Finishing
    * Step 7:  (Message: StatusNotification.req)  status is Available

Expected result(s) / behaviour
    n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus, Reason

from charge_point import TziChargePoint16
from reusable_states import authorized, charging
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_012(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: Reusable State Charging (Authorized → Charging)
    await authorized(cp, VALID_ID_TAG)
    start_response, transaction_id = await charging(cp, VALID_ID_TAG, CONNECTOR_ID)

    # Step 1-2: Wait for CSMS to send RemoteStopTransaction.req → CP responds Accepted
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'remote-stop-transaction', {'transactionId': transaction_id}))
    await asyncio.wait_for(cp._received_remote_stop.wait(), timeout=ACTION_TIMEOUT)
    assert cp._remote_stop_transaction_id == transaction_id

    # Step 3-4: StopTransaction with reason=Remote
    stop_response = await cp.send_stop_transaction(
        transaction_id=transaction_id,
        reason=Reason.remote,
        id_tag=VALID_ID_TAG,
    )
    assert stop_response is not None

    # Step 5-6: StatusNotification(Finishing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.finishing)

    # Step 7-8: EV driver unplugs cable → StatusNotification(Available)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.available)

    start_task.cancel()
