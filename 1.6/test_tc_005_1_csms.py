"""
Test case name      EV Side Disconnected - StopTransactionOnEVSideDisconnect = true -
                    UnlockConnectorOnEVSideDisconnect = true
Test case Id        TC_005_1_CSMS
OCPP Version        1.6j
Chapter             3.2.4 - Start Charging Session
System under test   Central System
Document Reference  CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf
                    Table 126, pages 112-113/176 (section 3.2.4)

Description         This scenario is used to stop the transaction when the cable is disconnected
                    at EV side.

Purpose             To test if the Central System can handle when the Charge Point stops the
                    transaction when the cable is disconnected at EV side, and it is configured
                    to do so.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      Charging

Test Scenario
1. [EV driver disconnects cable on EV side.]
   The Charge Point sends a StatusNotification.req to the Central System.
2. The Central System responds with a StatusNotification.conf.
3. The Charge Point sends a StopTransaction.req to the Central System.
4. The Central System responds with a StopTransaction.conf.
5. The Charge Point sends a StatusNotification.req to the Central System.
6. The Central System responds with a StatusNotification.conf.
7. [EV driver unplugs the cable from the Charge Point.]
   The Charge Point sends a StatusNotification.req to the Central System.
8. The Central System responds with a StatusNotification.conf.

Tool Validations
    Step 1 (Charge Point -> Central System):
        Message: StatusNotification.req
        - status is SuspendedEV
    Step 3 (Charge Point -> Central System):
        Message: StopTransaction.req
        - reason is EVDisconnected
    Step 5 (Charge Point -> Central System):
        Message: StatusNotification.req
        - status is Finishing
    Step 7 (Charge Point -> Central System):
        Message: StatusNotification.req
        - status is Available

Expected Result(s)  n/a (per official document)
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus, Reason

from charge_point import TziChargePoint16
from reusable_states import authorized, charging
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_005_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: Reusable State Charging (Authorized → Charging)
    await authorized(cp, VALID_ID_TAG)
    start_response, transaction_id = await charging(cp, VALID_ID_TAG, CONNECTOR_ID)

    # Step 1-2: EV driver disconnects cable on EV side → StatusNotification(SuspendedEV)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.suspended_ev)

    # Step 3-4: StopTransaction with reason=EVDisconnected
    stop_response = await cp.send_stop_transaction(
        transaction_id=transaction_id,
        reason=Reason.ev_disconnected,
        id_tag=VALID_ID_TAG,
    )
    assert stop_response is not None

    # Step 5-6: StatusNotification(Finishing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.finishing)

    # Step 7-8: EV driver unplugs cable from CP → StatusNotification(Available)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.available)

    start_task.cancel()
