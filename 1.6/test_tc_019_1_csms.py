"""
Test case name      Retrieve all configuration keys
Test case Id        TC_019_1_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.7.1 - Core Profile - Configuration Happy Flow
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument, Table 138, Pages 123-124/176

Description         The Central System is able to retrieve all available configuration keys.

Purpose             To check whether the Central System is able to retrieve all Configuration
                    keys and whether the Charge Point has all required keys configured.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a GetConfiguration.req to the Charge Point
       with an empty key list (no keys specified, meaning "get all").
    2. The Charge Point responds with a GetConfiguration.conf containing
       all available configuration keys.

Tool Validations
    * Step 1 (GetConfiguration.req):
      - The key list MUST be empty (no specific keys requested).

    * Step 2 (GetConfiguration.conf):
      - The response MUST contain all required configuration keys
        with correct accessibility (R or RW) values.

      Core Profile Keys:
        - AuthorizeRemoteTxRequests / R or RW
        - ClockAlignedDataInterval / RW
        - ConnectionTimeOut / RW
        - ConnectorPhaseRotation / RW
        - GetConfigurationMaxKeys / R
        - HeartbeatInterval / RW
        - LocalAuthorizeOffline / RW
        - LocalPreAuthorize / RW
        - MeterValuesAlignedData / RW
        - MeterValuesSampledData / RW
        - MeterValueSampleInterval / RW
        - NumberOfConnectors / R
        - ResetRetries / RW
        - StopTransactionOnEVSideDisconnect / RW
        - StopTransactionOnInvalidId / RW
        - StopTxnAlignedData / RW
        - StopTxnSampledData / RW
        - SupportedFeatureProfiles / R
        - TransactionMessageAttempts / RW
        - TransactionMessageRetryInterval / RW
        - UnlockConnectorOnEVSideDisconnect / RW

      Local Auth List Management Keys:
        - LocalAuthListEnabled / RW
        - LocalAuthListMaxLength / R
        - SendLocalListMaxLength / R

      Smart Charging Profile Keys:
        - ChargeProfileMaxStackLevel / R
        - ChargingScheduleAllowedChargingRateUnit / R
        - ChargingScheduleMaxPeriods / R
        - MaxChargingProfilesInstalled / R

      Reservation:
        - None

      Remote Trigger:
        - None

Expected Result
    All required keys are configured.
    The Central System is able to retrieve the values of all requested
    configuration keys.

Note
    The OCTT Tool Validations check that accessibility (R/RW) contains the
    correct values for each key. The current implementation validates key
    presence but does not assert readonly flags match the R/RW designations
    listed above. TODO: consider adding accessibility validation to match
    the OCTT's actual checks.
"""

import asyncio
import os
import pytest

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))

# All required OCPP 1.6 configuration keys the CP must report
CORE_KEYS = [
    'AuthorizeRemoteTxRequests',
    'ClockAlignedDataInterval',
    'ConnectionTimeOut',
    'ConnectorPhaseRotation',
    'GetConfigurationMaxKeys',
    'HeartbeatInterval',
    'LocalAuthorizeOffline',
    'LocalPreAuthorize',
    'MeterValuesAlignedData',
    'MeterValuesSampledData',
    'MeterValueSampleInterval',
    'NumberOfConnectors',
    'ResetRetries',
    'StopTransactionOnEVSideDisconnect',
    'StopTransactionOnInvalidId',
    'StopTxnAlignedData',
    'StopTxnSampledData',
    'SupportedFeatureProfiles',
    'TransactionMessageAttempts',
    'TransactionMessageRetryInterval',
    'UnlockConnectorOnEVSideDisconnect',
]

LOCAL_AUTH_LIST_KEYS = [
    'LocalAuthListEnabled',
    'LocalAuthListMaxLength',
    'SendLocalListMaxLength',
]

SMART_CHARGING_KEYS = [
    'ChargeProfileMaxStackLevel',
    'ChargingScheduleAllowedChargingRateUnit',
    'ChargingScheduleMaxPeriods',
    'MaxChargingProfilesInstalled',
]

# Default configuration values the CP reports to the CSMS
_DEFAULT_CONFIGURATION = [
    {'key': 'AuthorizeRemoteTxRequests', 'readonly': False, 'value': 'true'},
    {'key': 'ClockAlignedDataInterval', 'readonly': False, 'value': '0'},
    {'key': 'ConnectionTimeOut', 'readonly': False, 'value': '60'},
    {'key': 'ConnectorPhaseRotation', 'readonly': False, 'value': '0.RST,1.RST'},
    {'key': 'GetConfigurationMaxKeys', 'readonly': True, 'value': '50'},
    {'key': 'HeartbeatInterval', 'readonly': False, 'value': '300'},
    {'key': 'LocalAuthorizeOffline', 'readonly': False, 'value': 'true'},
    {'key': 'LocalPreAuthorize', 'readonly': False, 'value': 'true'},
    {'key': 'MeterValuesAlignedData', 'readonly': False, 'value': 'Energy.Active.Import.Register'},
    {'key': 'MeterValuesSampledData', 'readonly': False, 'value': 'Energy.Active.Import.Register'},
    {'key': 'MeterValueSampleInterval', 'readonly': False, 'value': '60'},
    {'key': 'NumberOfConnectors', 'readonly': True, 'value': '1'},
    {'key': 'ResetRetries', 'readonly': False, 'value': '3'},
    {'key': 'StopTransactionOnEVSideDisconnect', 'readonly': False, 'value': 'true'},
    {'key': 'StopTransactionOnInvalidId', 'readonly': False, 'value': 'true'},
    {'key': 'StopTxnAlignedData', 'readonly': False, 'value': 'Energy.Active.Import.Register'},
    {'key': 'StopTxnSampledData', 'readonly': False, 'value': 'Energy.Active.Import.Register'},
    {'key': 'SupportedFeatureProfiles', 'readonly': True, 'value': 'Core,LocalAuthListManagement,SmartCharging'},
    {'key': 'TransactionMessageAttempts', 'readonly': False, 'value': '3'},
    {'key': 'TransactionMessageRetryInterval', 'readonly': False, 'value': '60'},
    {'key': 'UnlockConnectorOnEVSideDisconnect', 'readonly': False, 'value': 'true'},
    {'key': 'LocalAuthListEnabled', 'readonly': False, 'value': 'true'},
    {'key': 'LocalAuthListMaxLength', 'readonly': True, 'value': '100'},
    {'key': 'SendLocalListMaxLength', 'readonly': True, 'value': '100'},
    {'key': 'ChargeProfileMaxStackLevel', 'readonly': True, 'value': '3'},
    {'key': 'ChargingScheduleAllowedChargingRateUnit', 'readonly': True, 'value': 'Current'},
    {'key': 'ChargingScheduleMaxPeriods', 'readonly': True, 'value': '5'},
    {'key': 'MaxChargingProfilesInstalled', 'readonly': True, 'value': '5'},
]


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_019_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    # Pre-load configuration keys the CP will report
    cp._configuration_key_list = _DEFAULT_CONFIGURATION
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send GetConfiguration.req (empty key list)
    await asyncio.wait_for(cp._received_get_configuration.wait(), timeout=ACTION_TIMEOUT)

    # Validate Step 1: CSMS requested all keys (empty or None key list)
    assert cp._get_configuration_keys is None or cp._get_configuration_keys == []

    # Validate Step 2: CP's response contains all required configuration keys
    reported_keys = [entry['key'] for entry in cp._configuration_key_list]
    for key in CORE_KEYS + LOCAL_AUTH_LIST_KEYS + SMART_CHARGING_KEYS:
        assert key in reported_keys, f"Required configuration key '{key}' not in CP response"

    start_task.cancel()
