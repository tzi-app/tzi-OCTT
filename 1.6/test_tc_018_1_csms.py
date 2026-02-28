"""
Test case name      Unlock Connector - With Charging Session (Not fixed cable)
Test case Id        TC_018_1_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.6. Core Profile - Unlocking Happy flow
                    3.6.3. Unlock Connector - With Charging Session
System under test   Central System (SUT)

Reference           CompliancyTestTool-TestCaseDocument (2025-11), Table 137, Page 122

Description         This scenario is used to unlock a connector of a Charge Point, while a
                    transaction is ongoing.

Purpose             To test if the Central System can handle when the Charge Point unlocks
                    the connector, when requested by the Central System.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): Charging

Test Scenario
    1. The Central System sends a UnlockConnector.req
    2. The Charge Point responds with a UnlockConnector.conf
    3. The Charge Point sends a StatusNotification.req
    4. The Central System responds with a StatusNotification.conf
    5. The Charge Point sends a StopTransaction.req
    6. The Central System responds with a StopTransaction.conf
    [EV driver unplugs the cable.]
    7. The Charge Point sends a StatusNotification.req
    8. The Central System responds with a StatusNotification.conf

Tool Validations
    * Step 2 (UnlockConnector.conf):
      - status is Unlocked
    * Step 3 (StatusNotification.req):
      - status is Finishing
    * Step 5 (StopTransaction.req):
      - reason is UnlockCommand
    * Step 7 (StatusNotification.req):
      - status is Available

Expected result(s) / behaviour
    n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus, Reason, UnlockStatus

from charge_point import TziChargePoint16
from reusable_states import booted, authorized, charging
from utils import get_basic_auth_headers
from trigger import trigger_v16

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_018_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    cp._unlock_response_status = UnlockStatus.unlocked
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: Reusable State Charging (Booted → Authorized → Charging)
    await booted(cp)
    await authorized(cp, VALID_ID_TAG)
    start_response, transaction_id = await charging(cp, VALID_ID_TAG, CONNECTOR_ID)

    # Step 1-2: Wait for CSMS to send UnlockConnector.req → CP responds Unlocked
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'unlock-connector', {'connectorId': CONNECTOR_ID}))
    await asyncio.wait_for(cp._received_unlock_connector.wait(), timeout=ACTION_TIMEOUT)

    # Step 3-4: StatusNotification(Finishing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.finishing)

    # Step 5-6: StopTransaction with reason=UnlockCommand
    stop_response = await cp.send_stop_transaction(
        transaction_id=transaction_id,
        reason=Reason.unlock_command,
        id_tag=VALID_ID_TAG,
    )
    assert stop_response is not None

    # Step 7-8: EV driver unplugs cable → StatusNotification(Available)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.available)

    start_task.cancel()
