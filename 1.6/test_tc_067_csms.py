"""
Test case name      Clear Charging Profile
Test case Id        TC_067_CSMS
Feature profile     SmartCharging (Section 3.19)
Document reference  CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf
                    Table 181, Section 3.19.3, Pages 154-155/176

Description         The Central System sets a Charging Profile and clears it.
Purpose             To check whether the Central System can clear a charging profile.
Prerequisite(s)     The Central System supports the Smart Charging feature profile.

Before State:
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): Charging
        NOTE: "Charging" references a reusable state (a transaction must be running
        on the Charge Point). Exact reusable state definition to be verified.

System under test   Central System

Test Scenario
    Manual Action: Set three different charging profiles. Steps 1-2 are therefor repeated three times.
    1. The Central System sends a SetChargingProfile.req to the Charge Point.
    2. The Charge Point responds with a SetChargingProfile.conf.
    (Repeated 3 times for 3 different charging profiles)

    Manual Action: Clear a charging profile based on ID.
    3. The Central System sends a ClearChargingProfile.req to the Charge Point.
    4. The Charge Point responds with a ClearChargingProfile.conf.

    Manual Action: Clear a charging profile based on criteria.
    5. The Central System sends a ClearChargingProfile.req to the Charge Point.
    6. The Charge Point responds with a ClearChargingProfile.conf.

    Manual Action: Clear all remaining charging profiles.
    7. The Central System sends a ClearChargingProfile.req to the Charge Point.
    8. The Charge Point responds with a ClearChargingProfile.conf.

Tool validations
    * Step 1 (SetChargingProfile.req) - Three charging profiles are set:
        Charging profile 1:
            - connectorId should be 0
            - chargingProfilePurpose should be ChargePointMaxProfile
            - stackLevel should be <Configured Stack Level>
            - transactionId should be <Omitted>
            - chargingProfileId should be <Different than the chargingProfileId from profile 2 and 3>

        Charging profile 2:
            - connectorId should be <Configured ConnectorId>
            - chargingProfilePurpose should be TxDefaultProfile
            - stackLevel should be <Configured Stack Level>
            - transactionId should be <Omitted>
            - chargingProfileId should be <Different than the chargingProfileId from profile 1 and 3>

        Charging profile 3:
            - connectorId should be <Configured ConnectorId>
            - chargingProfilePurpose should be TxProfile
            - stackLevel should be <Configured Stack Level>
            - transactionId should be <Generated transactionId by Central System>
            - chargingProfileId should be <Different than the chargingProfileId from profile 1 and 2>

        NOTE: The OCTT document specifies <Configured Stack Level> for all three profiles,
        implying the same stack level value is used across all profiles. No specific value
        is prescribed; the test validates that stackLevel is present and identical across
        all three profiles.

    * Step 2 (SetChargingProfile.conf) - for each of the 3 profiles:
        - status should be Accepted

    * Step 3 (ClearChargingProfile.req) - Clear by ID:
        - id should be <Generated Id from charging profile 1>
        - connectorId, chargingProfilePurpose, and stackLevel fields should be omitted

    * Step 4/6/8 (ClearChargingProfile.conf):
        - status should be Accepted

    * Step 5 (ClearChargingProfile.req) - Clear by criteria:
        - id should be omitted
        - connectorId should be <Configured ConnectorId>
        - chargingProfilePurpose should be TxDefaultProfile
        - stackLevel should be <Configured Stack Level>

    * Step 7 (ClearChargingProfile.req) - Clear all remaining:
        - All fields should be omitted

Expected result(s) / behaviour:
    Charge Point (Tool): n/a
    Central System (SUT): The Central System was able to clear the ChargingProfile of the Charge Point.
"""

import asyncio
import os
import pytest
from datetime import datetime, timedelta

from ocpp.v16.enums import ChargingProfileStatus, ClearChargingProfileStatus

from charge_point import TziChargePoint16
from reusable_states import booted, authorized, charging
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_067(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: Bring CP into Charging state
    await booted(cp)
    await authorized(cp, VALID_ID_TAG)
    start_response, transaction_id = await charging(cp, VALID_ID_TAG, CONNECTOR_ID)

    # Steps 1-2: Wait for 3 SetChargingProfile.req messages and capture each
    # Define 3 charging profiles to trigger
    _profile_payloads = [
        {
            'connectorId': 0,
            'csChargingProfiles': {
                'chargingProfileId': 100,
                'stackLevel': 1,
                'chargingProfilePurpose': 'ChargePointMaxProfile',
                'chargingProfileKind': 'Absolute',
                'validFrom': datetime.now().isoformat() + 'Z',
                'validTo': (datetime.now() + timedelta(days=1)).isoformat() + 'Z',
                'chargingSchedule': {
                    'startSchedule': datetime.now().isoformat() + 'Z',
                    'chargingRateUnit': 'A',
                    'duration': 86400,
                    'chargingSchedulePeriod': [{'startPeriod': 0, 'limit': 16.0, 'numberPhases': 3}],
                },
            },
        },
        {
            'connectorId': CONNECTOR_ID,
            'csChargingProfiles': {
                'chargingProfileId': 101,
                'stackLevel': 1,
                'chargingProfilePurpose': 'TxDefaultProfile',
                'chargingProfileKind': 'Absolute',
                'validFrom': datetime.now().isoformat() + 'Z',
                'validTo': (datetime.now() + timedelta(days=1)).isoformat() + 'Z',
                'chargingSchedule': {
                    'startSchedule': datetime.now().isoformat() + 'Z',
                    'chargingRateUnit': 'A',
                    'duration': 86400,
                    'chargingSchedulePeriod': [{'startPeriod': 0, 'limit': 16.0, 'numberPhases': 3}],
                },
            },
        },
        {
            'connectorId': CONNECTOR_ID,
            'csChargingProfiles': {
                'chargingProfileId': 102,
                'stackLevel': 1,
                'chargingProfilePurpose': 'TxProfile',
                'chargingProfileKind': 'Absolute',
                'transactionId': transaction_id,
                'validFrom': datetime.now().isoformat() + 'Z',
                'validTo': (datetime.now() + timedelta(days=1)).isoformat() + 'Z',
                'chargingSchedule': {
                    'startSchedule': datetime.now().isoformat() + 'Z',
                    'chargingRateUnit': 'A',
                    'duration': 86400,
                    'chargingSchedulePeriod': [{'startPeriod': 0, 'limit': 16.0, 'numberPhases': 3}],
                },
            },
        },
    ]

    profiles = []
    for i in range(3):
        if i > 0:
            cp._received_set_charging_profile.clear()
        asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'set-charging-profile', _profile_payloads[i]))
        await asyncio.wait_for(cp._received_set_charging_profile.wait(), timeout=ACTION_TIMEOUT)
        profiles.append(cp._set_charging_profile_data)

    assert cp._set_charging_profile_count >= 3

    # Validate profile 1: ChargePointMaxProfile on connector 0
    assert profiles[0]['connector_id'] == 0
    assert profiles[0]['cs_charging_profiles']['charging_profile_purpose'] == 'ChargePointMaxProfile'
    assert profiles[0]['cs_charging_profiles'].get('stack_level') is not None
    assert profiles[0]['cs_charging_profiles'].get('transaction_id') is None

    # Validate profile 2: TxDefaultProfile on configured connector
    assert profiles[1]['connector_id'] == CONNECTOR_ID
    assert profiles[1]['cs_charging_profiles']['charging_profile_purpose'] == 'TxDefaultProfile'
    assert profiles[1]['cs_charging_profiles'].get('stack_level') is not None
    assert profiles[1]['cs_charging_profiles'].get('transaction_id') is None

    # Validate profile 3: TxProfile on configured connector with transactionId
    assert profiles[2]['connector_id'] == CONNECTOR_ID
    assert profiles[2]['cs_charging_profiles']['charging_profile_purpose'] == 'TxProfile'
    assert profiles[2]['cs_charging_profiles'].get('stack_level') is not None
    assert profiles[2]['cs_charging_profiles'].get('transaction_id') == transaction_id

    # All charging profile IDs must be different
    profile_ids = [p['cs_charging_profiles']['charging_profile_id'] for p in profiles]
    assert len(set(profile_ids)) == 3

    # All stack levels should be the same (<Configured Stack Level>)
    stack_levels = [p['cs_charging_profiles']['stack_level'] for p in profiles]
    assert len(set(stack_levels)) == 1

    # Steps 3-8: Wait for 3 ClearChargingProfile.req messages and validate each
    _clear_payloads = [
        {'id': 100},
        {'connectorId': CONNECTOR_ID, 'chargingProfilePurpose': 'TxDefaultProfile', 'stackLevel': 1},
        {},
    ]

    clears = []
    for i in range(3):
        if i > 0:
            cp._received_clear_charging_profile.clear()
        asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'clear-charging-profile', _clear_payloads[i]))
        await asyncio.wait_for(cp._received_clear_charging_profile.wait(), timeout=ACTION_TIMEOUT)
        clears.append(cp._clear_charging_profile_data)

    assert cp._clear_charging_profile_count >= 3

    # Clear 1: by ID (profile 1's chargingProfileId), other fields omitted
    assert clears[0]['id'] == profile_ids[0]
    assert clears[0].get('connector_id') is None
    assert clears[0].get('charging_profile_purpose') is None
    assert clears[0].get('stack_level') is None

    # Clear 2: by criteria (connectorId + purpose + stackLevel, no id)
    assert clears[1].get('id') is None
    assert clears[1]['connector_id'] == CONNECTOR_ID
    assert clears[1]['charging_profile_purpose'] == 'TxDefaultProfile'
    assert clears[1]['stack_level'] is not None

    # Clear 3: all fields omitted (clear all remaining)
    assert clears[2].get('id') is None
    assert clears[2].get('connector_id') is None
    assert clears[2].get('charging_profile_purpose') is None
    assert clears[2].get('stack_level') is None

    start_task.cancel()
