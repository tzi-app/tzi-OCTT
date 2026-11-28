"""
Test case name      Stop transaction options - Deauthorized - timeout
Test case Id        TC_E_39_CSMS
Use case Id(s)      E03, E06
Requirement(s)      E03.FR.04, E03.FR.05, E06.FR.04

Requirement Details:
    E03.FR.04: (not found in OCPP 2.1 Part 2)
    E03.FR.05: The Charging Station SHOULD end the transaction and send a TransactionEventRequest (eventType =
               Ended, stoppedReason = Timeout, triggerReason = EVConnectionTimeout) to the CSMS.
        Precondition: When the EV Driver does not plug-in the charging cable before the timeout set by the
                      Configuration Variable: EVConnectionTimeOut AND TxStopPoint does not contain
                      ParkingBayOccupancy
        Note: This requirement is an additional safety measure to make sure the transaction is ended when the
              EVConnectionTimeOut is triggered. However it is up to the CSMS to make sure that sensible
              TxStartPoint / TxStopPoint combinations are configured. E.g. if Authorized is used as
              TxStartPoint, it should also be used as TxStopPoint.
    E06.FR.04: See use case E05 - Start Transaction - Id not Accepted,
        Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a
                      TransactionEventResponse
System under test   CSMS

Description         OCPP 2.x.x allows an EV driver to either first connect the EV and EVSE OR present a form
                    of identification. Both sequences will result in being able to charge.

Purpose             To verify if the CSMS is able to handle a Charging Station that deauthorizes the
                    transaction after the EVConnectionTimeout has expired.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized

Test Scenario
1. The Test System sends a TransactionEventRequest
    - With triggerReason is EVConnectTimeout
    - transactionInfo.stoppedReason is Timeout
    - eventType is Ended
    Note(s):
    - This step will be executed after the _<Configured EV connection timeout> expires._
2. The CSMS responds with a TransactionEventResponse

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
from reusable_states.authorized import authorized
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
# TxCtrlr.EVConnectionTimeOut of the Test System, in seconds
CONFIGURED_EV_CONNECTION_TIMEOUT = int(os.environ['CONFIGURED_EV_CONNECTION_TIMEOUT'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_39(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is Authorized
    transaction_id = await authorized(cp)

    # 1. The Test System sends a TransactionEventRequest
    #    - With triggerReason is EVConnectTimeout
    #    - transactionInfo.stoppedReason is Timeout
    #    - eventType is Ended
    #    Note(s): This step will be executed after the <Configured EV connection timeout>
    #    expires.
    # 2. The CSMS responds with a TransactionEventResponse
    await asyncio.sleep(CONFIGURED_EV_CONNECTION_TIMEOUT)
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='EVConnectTimeout',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'stopped_reason': 'Timeout'},
    ))

    start_task.cancel()
