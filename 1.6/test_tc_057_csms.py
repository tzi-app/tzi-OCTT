"""
Test case name      Central Smart Charging - TxProfile
Test case Id        TC_057_CSMS
Feature profile     SmartCharging

Document ref        Section 3.19.1, Table 179, pages 152-153/176
                    (CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf)

Description         The Central System sets a schedule for a running transaction.
Purpose             To check whether the Central System is able to set a schedule for a running transaction on a Charge Point.
Prerequisite(s)     The Central System supports the Smart Charging feature profile.

Before State:
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): Charging
        (Reusable state "Charging" is defined in Table 201, page 173/176.
         Requires Authorized state first, then: StatusNotification(Preparing) →
         StartTransaction → StatusNotification(Charging).)

System under test   Central System

Test Scenario
    1. The Central System sends a SetChargingProfile.req to the Charge Point.
    2. The Charge Point responds with a SetChargingProfile.conf.

Tool validations
    * Step 1:
        (Message: SetChargingProfile.req)
        - connectorId should be <Configured connectorId>
        - csChargingProfiles.chargingProfilePurpose should be TxProfile
        - csChargingProfiles.transactionId should be <Generated transactionId>
        - csChargingProfiles.recurrencyKind should be <Omitted>
        - csChargingProfiles.chargingProfileKind should be Absolute or Relative

        If csChargingProfiles.chargingProfileKind is Absolute:
            - csChargingProfiles.validFrom should be <Not omitted>
            - csChargingProfiles.validTo should be <Not omitted>
            - csChargingProfiles.chargingSchedule.startSchedule should be <Not omitted>
            - csChargingProfiles.chargingSchedule.duration should be <Not omitted>

        If csChargingProfiles.chargingProfileKind is Relative:
            - csChargingProfiles.chargingSchedule.startSchedule should be <Omitted>

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
from reusable_states import booted, authorized, charging
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
async def test_tc_057(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: Bring CP into Charging state
    await booted(cp)
    await authorized(cp, VALID_ID_TAG)
    start_response, transaction_id = await charging(cp, VALID_ID_TAG, CONNECTOR_ID)

    # Step 1-2: Wait for CSMS to send SetChargingProfile.req (TxProfile)
    await asyncio.wait_for(cp._received_set_charging_profile.wait(), timeout=ACTION_TIMEOUT)

    # Validate SetChargingProfile.req fields
    profile_data = cp._set_charging_profile_data
    assert profile_data is not None
    assert profile_data['connector_id'] == CONNECTOR_ID

    profile = profile_data['cs_charging_profiles']
    assert profile['charging_profile_purpose'] == 'TxProfile'
    assert profile.get('transaction_id') == transaction_id
    assert profile.get('recurrency_kind') is None  # must be omitted
    assert profile['charging_profile_kind'] in ('Absolute', 'Relative')

    schedule = profile['charging_schedule']
    if profile['charging_profile_kind'] == 'Absolute':
        assert profile.get('valid_from') is not None
        assert profile.get('valid_to') is not None
        assert schedule.get('start_schedule') is not None
        assert schedule.get('duration') is not None
    elif profile['charging_profile_kind'] == 'Relative':
        assert schedule.get('start_schedule') is None

    start_task.cancel()
