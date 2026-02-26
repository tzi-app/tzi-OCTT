"""
Test case name      Change/Set Configuration
Test case Id        TC_021_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.7.3 - Core Profile - Configuration Happy Flow
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument, Table 140, Page 125/176

Description         The Central System is able to change configuration.

Purpose             To test if the Central System is able to change a configuration key.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a ChangeConfiguration.req to the Charge Point
       with key = "MeterValueSampleInterval" and value = "60".
    2. The Charge Point responds with a ChangeConfiguration.conf with status = "Accepted".

Tool Validations
    * Step 1 (ChangeConfiguration.req):
      - key is "MeterValueSampleInterval"
    * Step 2 (ChangeConfiguration.conf):
      - status MUST be "Accepted"

Expected Result     n/a
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
async def test_tc_021(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    cp._change_configuration_response_status = ConfigurationStatus.accepted
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send ChangeConfiguration.req → CP responds Accepted
    await asyncio.wait_for(cp._received_change_configuration.wait(), timeout=ACTION_TIMEOUT)

    # Validate the CSMS sent the expected key and value
    assert cp._change_configuration_key == 'MeterValueSampleInterval'
    assert cp._change_configuration_value == '60'

    start_task.cancel()
