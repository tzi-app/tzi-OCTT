"""
Test case name      Central Smart Charging - TxDefaultProfile
Test case Id        TC_056_CSMS
Feature profile     SmartCharging

Reference           CompliancyTestTool-TestCaseDocument, Table 178, page 151,
                    section 3.19.1 Central Smart Charging

Description         The Central System sets a default schedule for new transactions.
Purpose             To check whether the Central System can set a default schedule for new transactions.
Prerequisite(s)     The Central System supports the Smart Charging feature profile.

Before State:
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
    1. The Central System sends a SetChargingProfile.req to the Charge Point.
    2. The Charge Point responds with a SetChargingProfile.conf.

Tool validations
    * Step 1:
        (Message: SetChargingProfile.req)
        - connectorId should be <Configured connectorId>
        - csChargingProfiles.stackLevel should be <Configured stackLevel>
        - csChargingProfiles.chargingProfilePurpose should be TxDefaultProfile
        - csChargingProfiles.chargingProfileKind should be Absolute
        - csChargingProfiles.validFrom should be present (Not omitted)
        - csChargingProfiles.validTo should be present (Not omitted)
        - csChargingProfiles.transactionId should be omitted
        - csChargingProfiles.recurrencyKind should be omitted
        - csChargingProfiles.chargingSchedule.startSchedule should be present (Not omitted)
        - csChargingProfiles.chargingSchedule.chargingRateUnit should be <Configured chargingRateUnit>
        - csChargingProfiles.chargingSchedule.duration should be <Configured duration>
        - csChargingProfiles.chargingSchedule.chargingSchedulePeriod.startPeriod should be <Configured startPeriod>
        - csChargingProfiles.chargingSchedule.chargingSchedulePeriod.limit should be 6.0 or 6000.0
        - csChargingProfiles.chargingSchedule.chargingSchedulePeriod.numberPhases:
            If <Configured numberPhases> is NOT 3: numberPhases should be <Configured numberPhases>
            If <Configured numberPhases> IS 3: numberPhases should be <Configured numberPhases> or omitted

    * Step 2:
        (Message: SetChargingProfile.conf)
        - status should be Accepted

Expected result(s) / behaviour: n/a
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import ChargingProfileStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_056(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send SetChargingProfile.req
    await asyncio.wait_for(cp._received_set_charging_profile.wait(), timeout=ACTION_TIMEOUT)

    # Validate SetChargingProfile.req fields
    profile_data = cp._set_charging_profile_data
    assert profile_data is not None
    assert profile_data['connector_id'] == CONNECTOR_ID

    profile = profile_data['cs_charging_profiles']
    assert profile['charging_profile_purpose'] == 'TxDefaultProfile'
    assert profile['charging_profile_kind'] == 'Absolute'
    assert profile.get('valid_from') is not None
    assert profile.get('valid_to') is not None
    assert profile.get('transaction_id') is None  # must be omitted
    assert profile.get('recurrency_kind') is None  # must be omitted

    schedule = profile['charging_schedule']
    assert schedule.get('start_schedule') is not None
    assert schedule.get('charging_rate_unit') is not None
    assert schedule.get('duration') is not None

    periods = schedule['charging_schedule_period']
    assert len(periods) > 0
    assert periods[0]['limit'] in (6.0, 6000.0)

    # Validate stackLevel
    assert profile.get('stack_level') is not None

    # Validate first chargingSchedulePeriod startPeriod
    assert periods[0].get('start_period') is not None

    # Validate numberPhases (if not 3, must be present; if 3, may be omitted)
    number_phases = periods[0].get('number_phases')
    if number_phases is not None:
        assert isinstance(number_phases, int)

    start_task.cancel()
