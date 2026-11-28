"""
Test case name      CustomData - Receive custom data
Test case Id        TC_P_03_CSMS
Use case Id(s)      N/a
Requirement(s)      N/a
System under test   CSMS

Description         Checks if the CSMS is able to receive custom data.

Purpose             To verify whether the CSMS is able to handle receiving custom data.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a StatusNotificationRequest with
    - customData <customData>
2. The CSMS responds with a StatusNotificationResponse
3. The Test System sends a TransactionEventRequest with
    - customData customData
    - transactionInfo.customData <customData>
4. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_VENDOR_ID = os.environ['CONFIGURED_VENDOR_ID']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])

# <customData>: vendor-specific data, which every object of a message may have
CUSTOM_DATA = {'vendorId': CONFIGURED_VENDOR_ID, 'octtTestCase': 'TC_P_03_CSMS', 'sequence': 1}


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_p_03(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The Test System sends a StatusNotificationRequest with
    #    - customData <customData>
    # 2. The CSMS responds with a StatusNotificationResponse
    await cp.call(call.StatusNotification(
        timestamp=utc_now_iso(),
        connector_status='Available',
        evse_id=CONFIGURED_EVSE_ID,
        connector_id=CONFIGURED_CONNECTOR_ID,
        custom_data=CUSTOM_DATA,
    ))

    # 3. The Test System sends a TransactionEventRequest with
    #    - customData <customData>
    #    - transactionInfo.customData <customData>
    # 4. The CSMS responds with a TransactionEventResponse
    transaction_id = cp.session.start_transaction()
    await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='EVDetected',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'custom_data': CUSTOM_DATA},
        custom_data=CUSTOM_DATA,
    ))

    start_task.cancel()
