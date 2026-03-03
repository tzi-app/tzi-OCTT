"""
Test case name      Reservation of a Charge Point - Transaction
Test case Id        TC_049_CSMS
OCPP Version        1.6J
Section             3.17.2 - Reservation of a Charge Point
Document Reference  Table 172, Section 3.17.2, document pages 146-147 / PDF pages 43-44
                    (CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf)

Description         A Charge Point / unspecified Connector is reserved and a charging
                    transaction takes place.

Purpose             Check whether Central System trigger the Charge Point to reserve
                    an unspecified Connector.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    Charge Point (Tool)                         Central System (SUT)
    ───────────────────                         ────────────────────
                                                1. The Central System sends a ReserveNow.req
                                                   with a reservationId, connectorId and idTag
                                                   to the Charge Point
    2. The Charge Point sends a
       ReserveNow.conf message to the
       Central System
    3. The Charge Point sends a
       StatusNotification.req to the
       Central System
                                                4. The Central System sends a
                                                   StatusNotification.conf to the Charge Point

Tool validations (Charge Point side):
* Step 3:
    Message: StatusNotification.req
    - The status is Reserved

Tool validations (Central System side):
* Step 1:
    Message: ReserveNow.req
    - The connectorId is 0

Expected result(s) / behaviour:
    Charge Point:
        The Charge Point handles the reservation correctly, only the idTag
        from the reservation can charge, on any available connector of the
        Charge Point.
    Central System:
        The Central System accepts the reservation for the right idTag and
        reservationId.

Notes (to be verified/fixed later):
    - The doc's Purpose text has a grammar issue ("trigger" instead of
      "triggers" or "can trigger") -- kept as-is from the document.
    - ReserveNow.req requires an expiryDate field per the OCPP 1.6 spec, but
      the document's scenario step 1 only explicitly mentions reservationId,
      connectorId, and idTag. The expiryDate should still be set to a future
      timestamp in the implementation.
    - The title says "Transaction" and the description says "a charging
      transaction takes place", but the scenario only has 4 steps with NO
      transaction flow (no Authorize, StartTransaction, Charging
      StatusNotification, etc.). Compare with TC_046 (Reservation of a
      Connector - Transaction) which explicitly includes a Reusable State:
      Charging step with the full transaction sub-flow. This appears to be an
      omission in the OCTT document for TC_049 — verify whether the OCTT tool
      actually expects a transaction after the reservation.
"""

import asyncio
import os
import pytest
from datetime import datetime, timedelta

from ocpp.v16.enums import ChargePointStatus

from charge_point import TziChargePoint16
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
VALID_ID_TAG = os.environ.get('VALID_ID_TOKEN', 'TEST_TAG')


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_049(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ReserveNow.req → CP responds Accepted
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'reserve-now', {
        'connectorId': 0,
        'expiryDate': (datetime.now() + timedelta(hours=1)).isoformat() + 'Z',
        'idTag': VALID_ID_TAG,
        'reservationId': 1,
    }))
    await asyncio.wait_for(cp._received_reserve_now.wait(), timeout=ACTION_TIMEOUT)
    assert cp._reserve_now_data is not None
    # Validate that connectorId is 0 (reservation of the whole Charge Point)
    assert cp._reserve_now_data['connector_id'] == 0

    # Step 3-4: CP sends StatusNotification(Reserved)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.reserved)

    start_task.cancel()
