"""
Test case name      Configuration keys - NotSupported
Test case Id        TC_040_1_CSMS
OCPP version        1.6J
Profile             Core

Document Reference  OCTT CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf
                    Section 3.13 - Core Profile - Configuration Keys Non-Happy Flow
                    Section 3.13.1 - Configuration keys - NotSupported
                    Table 153, Document Page 134, PDF Page 31

System under test   Central System

Description         This scenario is used to reject an unknown configuration key.

Purpose             To test if the Central System is able to handle a Charge Point that does not support a given
                    configuration key.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System (SUT) sends a ChangeConfiguration.req to the Charge Point (OCTT).
   - Message: ChangeConfiguration.req
   - Fields: not specified in test case document (SUT decides key and value)
2. The Charge Point (OCTT) responds with a ChangeConfiguration.conf.
   - Message: ChangeConfiguration.conf
   - Fields:
       status (ConfigurationStatus) - NotSupported

Tool validations
* Charge Point (Tool):
  Step 2:
  (Message: ChangeConfiguration.conf)
  The status is NotSupported
* Central System (SUT):
  n/a

Expected result(s) / behaviour
    Charge Point (Tool):     n/a
    Central System (SUT):    n/a

Notes (to be fixed later)
    - The test case document does not specify which key/value the Central System (SUT) should send
      in the ChangeConfiguration.req. The CS version (TC_040_1_CS) uses key="Testing", value="true"
      when the tool sends the request, but for the CSMS version the SUT decides.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ConfigurationStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_040_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # CP responds NotSupported for unknown configuration key
    cp._change_configuration_response_status = ConfigurationStatus.not_supported
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ChangeConfiguration.req → CP responds NotSupported
    await asyncio.wait_for(cp._received_change_configuration.wait(), timeout=ACTION_TIMEOUT)
    assert cp._change_configuration_key is not None

    start_task.cancel()
