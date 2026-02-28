"""
Test case name      Unlock connector - no charging session running (Fixed cable)
Test case Id        TC_017_2_CSMS
Test document       CompliancyTestTool-TestCaseDocument-CSMS-Section3 (2025-11),
                    Table 136, Section 3.6.2, page 121/176 (PDF page 18/73)
OCPP Version        1.6J
Profile             Core
Section             3.6.2 Unlock connector - no charging session running (Fixed cable)
System under test   Central System (CSMS)

Description         This scenario describes how the Charge Point should react to an
                    UnlockConnector.req, when having a fixed cable.

Purpose             To test if the Central System can handle when the Charge Point notifies
                    the Central System that it does not support the unlocking of a connector.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. The Central System sends an UnlockConnector.req to the Charge Point.
    2. The Charge Point responds with an UnlockConnector.conf.

Tool Validations
    * Step 2 (UnlockConnector.conf):
      - status MUST be "NotSupported"

Expected Result(s) / Behaviour
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

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_017_2(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # Fixed cable → CP responds NotSupported
    cp._unlock_response_status = UnlockStatus.not_supported
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send UnlockConnector.req → CP responds NotSupported
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'unlock-connector', {'connectorId': CONNECTOR_ID}))
    await asyncio.wait_for(cp._received_unlock_connector.wait(), timeout=ACTION_TIMEOUT)
    assert cp._unlock_connector_id is not None

    start_task.cancel()
