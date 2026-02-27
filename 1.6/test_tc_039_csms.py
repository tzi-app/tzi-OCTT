"""
Test case name      Offline Transaction
Test case Id        TC_039_CSMS
OCPP version        1.6J
Profile             Core
Section             3.12.3
Table               152
Document page       132-133/176
PDF reference       CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, physical pages 29-30

Description         This scenario is used to start and stop a transaction, while the Charge
                    Point is offline.

Purpose             To test if the Central System is able to handle queued transaction-related
                    messages, after a Charge Point comes back online again.

System under test   Central System (SUT)

Prerequisite(s)     n/a

Configuration State(s):
    n/a

Memory State(s):
    n/a

Reusable State(s):
    n/a

Test Scenario
    [Remove connectivity between Charge Point and Central System.]
    [EV Driver starts offline a transaction.]
    [EV Driver stops offline a transaction.]
    [EV driver unplugs the cable.]
    [Restore connectivity between Charge Point and Central System.]

1. The Charge Point sends a StartTransaction.req
2. The Central System responds with a StartTransaction.conf
3. The Charge Point sends a StopTransaction.req
4. The Central System responds with a StopTransaction.conf

    NOTE: The official test case document does not include field-level details for the
    steps above (e.g. connectorId, idTag, meterStart, timestamp for StartTransaction.req;
    transactionId, meterStop, timestamp for StopTransaction.req). These are inferred from
    the OCPP 1.6 specification and may be sent by the OCTT tool (to be verified).

Tool validations
* Step 3:
    (Message: StopTransaction.req)
    reason is Local
* Step 2:
    (Message: StartTransaction.conf)
    idTagInfo.status is Accepted

Expected result(s) / behaviour
    n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import AuthorizationStatus, Reason

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_039(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: StartTransaction with valid idTag (offline scenario)
    start_response = await cp.send_start_transaction(CONNECTOR_ID, VALID_ID_TAG)
    assert start_response.id_tag_info['status'] == AuthorizationStatus.accepted
    transaction_id = start_response.transaction_id

    # Step 3-4: StopTransaction with reason=Local
    stop_response = await cp.send_stop_transaction(
        transaction_id=transaction_id,
        reason=Reason.local,
        id_tag=VALID_ID_TAG,
    )
    assert stop_response is not None

    start_task.cancel()
