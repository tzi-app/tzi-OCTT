"""
Test case name      Get Composite Schedule
Test case Id        TC_066_CSMS
Feature profile     SmartCharging
Reference           OCTT TestCaseDocument Section 3.19.2, Table 180, Page 153/176

Description         The Central System requests a composite schedule.
Purpose             To check whether the Central System is able to request a composite schedule.
Prerequisite(s)     The Central System supports the Smart Charging feature profile.

Before State:
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
    1. The Central System sends a GetCompositeSchedule.req to the Charge Point.
    2. The Charge Point responds with a GetCompositeSchedule.conf containing a hard-coded composite schedule.

Tool validations
    * Step 1:
        (Message: GetCompositeSchedule.req)
        - connectorId should be <Configured ConnectorId>
        - duration should be <Configured Charging Schedule Duration>
        - chargingRateUnit should be <Configured Charging Rate Unit>
        NOTE: The OCTT doc says "Configured Charging Schedule Duration" and "Configured Charging Rate Unit"
              but does not specify exact values. The test asserts these fields are present (not None)
              and validates connectorId matches the configured connector.

    * Step 2:
        (Message: GetCompositeSchedule.conf)
        - chargingSchedule contains a hard-coded composite schedule
        NOTE: The conf includes status=Accepted, connector_id, schedule_start (current time),
              and a charging_schedule with one period (start_period=0, limit=16.0A).

Expected result(s):
    The Central System has retrieved the composite ChargingProfile.

Post scenario validations: N/a
"""

import asyncio
import os
import pytest

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers, now_iso

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_066(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)

    # Pre-configure composite schedule response
    cp._get_composite_schedule_response = {
        'connector_id': CONNECTOR_ID,
        'schedule_start': now_iso(),
        'charging_schedule': {
            'charging_rate_unit': 'A',
            'charging_schedule_period': [
                {'start_period': 0, 'limit': 16.0}
            ],
        },
    }

    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send GetCompositeSchedule.req
    await asyncio.wait_for(cp._received_get_composite_schedule.wait(), timeout=ACTION_TIMEOUT)
    data = cp._get_composite_schedule_data
    assert data is not None
    assert data['connector_id'] == CONNECTOR_ID
    assert data['duration'] is not None
    assert data['charging_rate_unit'] is not None

    start_task.cancel()
