"""
Test case name      Configuration keys - Invalid value
Test case Id        TC_040_2_CSMS
OCPP version        1.6J
Profile             Core
Document ref        Section 3.13.2, Table 154, Page 134/176
                    (CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, PDF page 31)

System under test   Central System

Description         This scenario is used to reject setting a configuration key, when an incorrect
                    value is given.

Purpose             To test if the Central System is able to handle a Charge Point rejecting setting
                    a configuration key.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System (SUT) sends a ChangeConfiguration.req.
2. The Charge Point (Tool) responds with a ChangeConfiguration.conf.

Tool validations
* Step 1:
  (Message: ChangeConfiguration.req)
  The key is MeterValueSampleInterval.
* Step 2:
  (Message: ChangeConfiguration.conf)
  The status is Rejected.

Expected result(s) / behaviour
    Charge Point (Tool):    n/a
    Central System (SUT):   n/a

Note: The test case document does not specify which value to send in ChangeConfiguration.req.
      The tool only validates that key = MeterValueSampleInterval and that the response
      status = Rejected. The actual value sent is implementation-dependent (to be confirmed).
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ConfigurationStatus

from charge_point import TziChargePoint16
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_040_2(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # CP responds Rejected for invalid configuration value
    cp._change_configuration_response_status = ConfigurationStatus.rejected
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ChangeConfiguration.req → CP responds Rejected
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'change-configuration', {'key': 'MeterValueSampleInterval', 'value': 'invalid'}))
    await asyncio.wait_for(cp._received_change_configuration.wait(), timeout=ACTION_TIMEOUT)
    assert cp._change_configuration_key == 'MeterValueSampleInterval'

    start_task.cancel()
