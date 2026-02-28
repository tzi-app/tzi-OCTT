"""
Test case name      Unlock Connector – Unknown Connector
Test case Id        TC_031_CSMS
OCPP Version        1.6J
Profile             Core
Document ref        CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf
                    Section 3.10.2, Table 148, Page 129/176

Description         This scenario is used to reject an UnlockConnector.req, when an unknown
                    connectorId is given.

Purpose             To test if the Central System is able to handle a Charge Point that does
                    not support UnlockConnector.req.

NOTE: The test name says "Unknown Connector" (connectorId doesn't exist) but the purpose says
"does not support UnlockConnector.req" (operation unsupported). Both map to status=NotSupported
per the OCPP 1.6 spec. This ambiguity comes from the official OCTT test document.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    Charge Point (Tool)                          Central System (SUT)
    -----------------------------------------    -----------------------------------------
                                                 1. The Central System sends a
                                                    UnlockConnector.req
    2. The Charge Point responds with a
       UnlockConnector.conf

Tool validations
    * Step 2 (Charge Point):
        (Message: UnlockConnector.conf)
        status is NotSupported
    * Central System side: n/a

Expected result(s) / behaviour
    n/a
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


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_031(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # Unknown connector → CP responds NotSupported
    cp._unlock_response_status = UnlockStatus.not_supported
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send UnlockConnector.req → CP responds NotSupported
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'unlock-connector', {'connectorId': 99}))
    await asyncio.wait_for(cp._received_unlock_connector.wait(), timeout=ACTION_TIMEOUT)
    assert cp._unlock_connector_id is not None

    start_task.cancel()
