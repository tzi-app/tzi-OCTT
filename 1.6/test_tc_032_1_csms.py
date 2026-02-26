"""
Test case name      Power Failure Boot - Stop Transactions
Test case Id        TC_032_1_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.11.1 - Core Profile - Power Failure
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument, Table 151, Page 131/176

Description         This scenario simulates a power failure during an active transaction.
                    After reboot the Charge Point stops any interrupted transactions.

Purpose             To test if the Central System can handle when the Charge Point reboots
                    after a power failure and stops the transaction that was active.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): Charging (Authorized → Charging)

Test Scenario
    [Power failure occurs.]
    1. The Charge Point sends a BootNotification.req
    2. The Central System responds with a BootNotification.conf
    [Send per connector and connectorId=0.]
    3. The Charge Point sends a StatusNotification.req
    4. The Central System responds with a StatusNotification.conf
    5. The Charge Point sends a StopTransaction.req
    6. The Central System responds with a StopTransaction.conf

Tool Validations
    * Step 2 (BootNotification.conf): status is Accepted
    * Step 3 (StatusNotification.req): status is Available (for non-charging connectors)
    * Step 5 (StopTransaction.req): reason is PowerLoss

Expected Result     n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargePointStatus, Reason, RegistrationStatus

from charge_point import TziChargePoint16
from reusable_states import authorized, charging
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_032_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: Reusable State Charging (Authorized → Charging)
    await authorized(cp, VALID_ID_TAG)
    start_response, transaction_id = await charging(cp, VALID_ID_TAG, CONNECTOR_ID)

    # [Power failure occurs — CP reboots]

    # Step 1-2: BootNotification after reboot
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    # Step 3-4: StatusNotification per connector and connectorId=0
    # The transaction connector reports Finishing; other connectors report Available
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.finishing)
    await cp.send_status_notification(0, status=ChargePointStatus.available)

    # Step 5-6: StopTransaction with reason=PowerLoss for the interrupted transaction
    stop_response = await cp.send_stop_transaction(
        transaction_id=transaction_id,
        reason=Reason.power_loss,
        id_tag=VALID_ID_TAG,
    )
    assert stop_response is not None

    start_task.cancel()
