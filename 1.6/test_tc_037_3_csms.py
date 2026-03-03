"""
Test case name      Offline Start Transaction - Invalid IdTag - StopTransactionOnInvalidId = true
Test case Id        TC_037_3_CSMS
OCPP version        1.6J
Profile             Core
Section             3.12.2
Reference           CompliancyTestTool-TestCaseDocument, Pages 131-132, Table 151

Description         This scenario is used to start a transaction, while being offline.

Purpose             To test if the Central System can handle when a Charge Point starts a transaction,
                    while being offline and queues transaction-related messages, after restoring the
                    connection.

System under test   Central System (SUT)

Prerequisite(s)     n/a

Configuration State(s):
    n/a
    NOTE: The test title implies the CP has StopTransactionOnInvalidId = true,
    which causes it to stop the transaction after receiving Invalid from the CSMS.
    This is a CP-side configuration, not a CSMS configuration.

Memory State(s):
    n/a

Reusable State(s):
    n/a

Test Scenario
    [Remove connectivity between Charge Point and Central System.]
    [EV Driver starts offline a transaction with an invalid idTag.]
    [Restore connectivity between Charge Point and Central System.]

1. The Charge Point sends a StartTransaction.req to the Central System.
    - connectorId: <Configured connectorId>
    - idTag: <Configured invalid idTag>
    - meterStart: <meter value at transaction start>
    - timestamp: <timestamp of transaction start (while offline)>
2. The Central System responds with a StartTransaction.conf.
3. The Charge Point sends a StatusNotification.req to the Central System.
    - connectorId: <Configured connectorId>
    - errorCode: NoError
    - status: Charging
4. The Central System responds with a StatusNotification.conf.
5. The Charge Point sends a StopTransaction.req to the Central System.
    - transactionId: <transactionId from Step 2>
    - reason: DeAuthorized
    - meterStop: <meter value at transaction stop>
    - timestamp: <timestamp of transaction stop>
6. The Central System responds with a StopTransaction.conf.
7. The Charge Point sends a StatusNotification.req to the Central System.
    - connectorId: <Configured connectorId>
    - errorCode: NoError
    - status: Finishing
8. The Central System responds with a StatusNotification.conf.

Tool validations
* Step 2:
    (Message: StartTransaction.conf)
    idTagInfo.status is Invalid
* Step 3:
    (Message: StatusNotification.req)
    status is Charging
* Step 5:
    (Message: StopTransaction.req)
    reason is DeAuthorized
* Step 7:
    (Message: StatusNotification.req)
    status is Finishing

Expected result(s) / behaviour
    n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import AuthorizationStatus, ChargePointStatus, Reason

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
INVALID_ID_TAG = os.environ['INVALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_037_3(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: StartTransaction with invalid idTag → expect Invalid
    start_response = await cp.send_start_transaction(CONNECTOR_ID, INVALID_ID_TAG)
    assert start_response.id_tag_info['status'] == AuthorizationStatus.invalid
    transaction_id = start_response.transaction_id

    # Step 3-4: StatusNotification(Charging)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.charging)

    # Step 5-6: StopTransaction with reason=DeAuthorized
    stop_response = await cp.send_stop_transaction(
        transaction_id=transaction_id,
        reason=Reason.de_authorized,
    )
    assert stop_response is not None

    # Step 7-8: StatusNotification(Finishing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.finishing)

    start_task.cancel()
