"""
Test case name      Remote unlock Connector - Without ongoing transaction - Accepted
Test case Id        TC_F_06_CSMS
Use case Id(s)      F05
Requirement(s)      n/a
System under test   CSMS

Description         This test case describes how the CSMS can be requested to sent an UnlockConnectorRequest
                    to the charging station. It sometimes happens that a connector of a Charging Station
                    socket does not unlock correctly. This happens most of the time when there is tension on
                    the charging cable. This means the driver cannot unplug his charging cable from the
                    Charging Station. To help a driver, the CSO can send a UnlockConnectorRequest to the
                    Charging Station. The Charging Station will then try to unlock the connector again.

Purpose             To verify if the CSMS is able to perform the remote unlock connector mechanism as
                    described at the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a UnlockConnectorRequest
2. The Test System responds with a UnlockConnectorResponse with status Unlocked

Tool validations
* Step 1:
    Message UnlockConnectorRequest
    - evseId <Configured evseId>
    - connectorId <Configured connectorId>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_f_06(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a UnlockConnectorRequest
    # 2. The Test System responds with a UnlockConnectorResponse with status Unlocked
    cp.set_response('UnlockConnector', status='Unlocked')
    request = await cp.wait_for_request(
        'UnlockConnector',
        manual_action=send_call(BASIC_AUTH_CP, 'UnlockConnector', {
            'evseId': CONFIGURED_EVSE_ID,
            'connectorId': CONFIGURED_CONNECTOR_ID,
        }))
    assert request.evse_id == CONFIGURED_EVSE_ID, \
        f"Expected UnlockConnectorRequest.evseId {CONFIGURED_EVSE_ID}, got {request.evse_id}"
    assert request.connector_id == CONFIGURED_CONNECTOR_ID, \
        f"Expected UnlockConnectorRequest.connectorId {CONFIGURED_CONNECTOR_ID}, got {request.connector_id}"

    start_task.cancel()
