"""
Test case name      Retrieve Specific Configuration Key
Test case Id        TC_019_2_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.7.2 - Core Profile - Configuration Happy Flow
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf,
                    Table 139, Pages 124-125/176

Description         The Central System is able to retrieve a specific configuration key.

Purpose             To check whether the Central System is able to retrieve a specific
                    Configuration key.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a GetConfiguration.req message to the Charge Point.
    2. The Charge Point responds with a GetConfiguration.conf.

Tool Validations
    * Step 1 (GetConfiguration.req):
      - key is "SupportedFeatureProfiles"
    * Step 2 (GetConfiguration.conf):
      - unknownKey list is <Empty>
      - configurationKey.key should be "SupportedFeatureProfiles"

Expected Result
    The Central System is able to retrieve the value of the requested
    configuration key.
"""

import asyncio
import os
import pytest

from charge_point import TziChargePoint16
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_019_2(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # Pre-load the specific key the CSMS will request
    cp._configuration_key_list = [
        {'key': 'SupportedFeatureProfiles', 'readonly': True,
         'value': 'Core,LocalAuthListManagement,SmartCharging'},
    ]
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send GetConfiguration.req with specific key
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'get-configuration', {'key': ['SupportedFeatureProfiles']}))
    await asyncio.wait_for(cp._received_get_configuration.wait(), timeout=ACTION_TIMEOUT)

    # Validate Step 1: CSMS requested "SupportedFeatureProfiles"
    assert cp._get_configuration_keys is not None
    assert 'SupportedFeatureProfiles' in cp._get_configuration_keys

    # Validate Step 2: unknownKey list is empty, configurationKey contains SupportedFeatureProfiles
    reported_keys = [entry['key'] for entry in cp._configuration_key_list]
    assert 'SupportedFeatureProfiles' in reported_keys
    # Validate unknownKey is empty: all requested keys exist in our configuration
    for key in (cp._get_configuration_keys or []):
        assert key in reported_keys, f"Key '{key}' not in configuration — would appear in unknownKey list"

    start_task.cancel()
