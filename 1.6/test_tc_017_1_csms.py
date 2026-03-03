"""
Test case name      Unlock connector - no charging session running (Not fixed cable)
Test case Id        TC_017_1_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.6.1 Core Profile - Unlocking Happy Flow
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument, Table 135, Page 121

Description         This scenario is used to unlock a connector of a Charge Point.

Purpose             To test if the Central System can handle when the Charge Point unlocks
                    the connector, when requested by the Central System.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a UnlockConnector.req
    2. The Charge Point responds with a UnlockConnector.conf

Tool Validations
    * Step 2 (Message: UnlockConnector.conf):
      - status is "Unlocked"

Expected result(s) / behaviour
    n/a

OCPP 1.6 Messages
    UnlockConnector.req:
        - connectorId (Required, integer): The identifier of the connector to be unlocked.
    UnlockConnector.conf:
        - status (Required, UnlockStatus): Indicates whether the connector has been unlocked.
          Accepted values: Unlocked, UnlockFailed, NotSupported
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import UnlockStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers
from trigger import trigger_v16

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_017_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # CP responds with Unlocked (default)
    cp._unlock_response_status = UnlockStatus.unlocked
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send UnlockConnector.req → CP responds Unlocked
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'unlock-connector', {'connectorId': CONNECTOR_ID}))
    await asyncio.wait_for(cp._received_unlock_connector.wait(), timeout=ACTION_TIMEOUT)
    assert cp._unlock_connector_id is not None

    start_task.cancel()
