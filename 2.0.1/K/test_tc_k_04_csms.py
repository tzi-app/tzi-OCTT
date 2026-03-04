"""
TC_K_04 - Replace charging profile - With chargingProfileId
Use case: n/a | Requirements: n/a
System under test: CSMS

Description:
    To verify if the CSMS is able to replace a charging profile with the same ProfileKind, Purpose, and
    stackLevel, but a different limit.

Main:
    1. The CSMS sends a SetChargingProfileRequest with limit 8.0 or 8000.0
    2. The OCTT responds with a SetChargingProfileResponse with status Accepted
    3. The CSMS sends a SetChargingProfileRequest with limit 6.0 or 6000.0
    4. The OCTT responds with a SetChargingProfileResponse with status Accepted

Tool validations:
    * Step 1:
      - chargingSchedulePeriod.startPeriod 0
      - chargingSchedulePeriod.limit 8.0 or 8000.0
      - chargingSchedule contains only one chargingSchedulePeriod
    * Step 3:
      - chargingSchedulePeriod.startPeriod 0
      - chargingSchedulePeriod.limit 6.0 or 6000.0
      - chargingSchedule contains only one chargingSchedulePeriod
    * Step 1/3:
      - chargingProfile.id <Same id for both chargingProfiles>
      - chargingSchedule.startSchedule must NOT be omitted
      - chargingProfile.stackLevel <Configured stackLevel>
      - chargingProfile.chargingProfilePurpose <Equal value for both> (TxDefaultProfile OR ChargingStationMaxProfile)
      - chargingProfile.chargingProfileKind <Equal value for both>
      - If purpose is TxDefaultProfile then kind must be Absolute OR Recurring
      - If purpose is ChargingStationMaxProfile then kind must be Absolute
      - If kind is Recurring then recurrencyKind must NOT be omitted, else omitted
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.routing import on
from ocpp.v201 import call_result
from ocpp.v201.enums import (
    Action,
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    ChargingProfileStatusEnumType,
    ChargingProfilePurposeEnumType,
    ChargingProfileKindEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


class SmartChargingMockCP(TziChargePoint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_charging_profile_count = 0
        self._set_charging_profile_requests = []
        self._all_profiles_received = asyncio.Event()

    @on(Action.set_charging_profile)
    async def on_set_charging_profile(self, evse_id, charging_profile, **kwargs):
        logging.info(f"Received SetChargingProfileRequest #{self._set_charging_profile_count + 1}: "
                     f"evse_id={evse_id}, profile={charging_profile}")
        self._set_charging_profile_requests.append({
            'evse_id': evse_id,
            'charging_profile': charging_profile,
        })
        self._set_charging_profile_count += 1
        if self._set_charging_profile_count >= 2:
            self._all_profiles_received.set()
        return call_result.SetChargingProfile(
            status=ChargingProfileStatusEnumType.accepted
        )


@pytest.mark.asyncio
async def test_tc_k_04():
    """Replace charging profile - With chargingProfileId."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)

    cp = SmartChargingMockCP(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Wait for both SetChargingProfileRequests
    await asyncio.wait_for(
        cp._all_profiles_received.wait(),
        timeout=CSMS_ACTION_TIMEOUT * 2,
    )

    assert len(cp._set_charging_profile_requests) >= 2

    profile1 = cp._set_charging_profile_requests[0]['charging_profile']
    profile2 = cp._set_charging_profile_requests[1]['charging_profile']

    # Extract schedule data for both profiles
    schedules1 = profile1.get('charging_schedule') or profile1.get('chargingSchedule')
    schedule1 = schedules1[0] if isinstance(schedules1, list) else schedules1
    periods1 = schedule1.get('charging_schedule_period') or schedule1.get('chargingSchedulePeriod')

    schedules2 = profile2.get('charging_schedule') or profile2.get('chargingSchedule')
    schedule2 = schedules2[0] if isinstance(schedules2, list) else schedules2
    periods2 = schedule2.get('charging_schedule_period') or schedule2.get('chargingSchedulePeriod')

    # Step 1: startPeriod must be 0 and limit 8.0 or 8000.0, only one period
    assert len(periods1) == 1, f"Expected first chargingSchedule to contain only one period, got {len(periods1)}"
    start_period1 = periods1[0].get('start_period') if periods1[0].get('start_period') is not None else periods1[0].get('startPeriod')
    assert start_period1 == 0, f"Expected first startPeriod=0, got {start_period1}"
    limit1 = periods1[0].get('limit')
    assert limit1 in (8.0, 8000.0), f"Expected first limit=8.0 or 8000.0, got {limit1}"

    # Step 3: startPeriod must be 0 and limit 6.0 or 6000.0, only one period
    assert len(periods2) == 1, f"Expected second chargingSchedule to contain only one period, got {len(periods2)}"
    start_period2 = periods2[0].get('start_period') if periods2[0].get('start_period') is not None else periods2[0].get('startPeriod')
    assert start_period2 == 0, f"Expected second startPeriod=0, got {start_period2}"
    limit2 = periods2[0].get('limit')
    assert limit2 in (6.0, 6000.0), f"Expected second limit=6.0 or 6000.0, got {limit2}"

    # Both should have the same chargingProfile.id
    id1 = profile1.get('id')
    id2 = profile2.get('id')
    assert id1 == id2, f"Expected same chargingProfile.id, got {id1} and {id2}"

    # startSchedule must NOT be omitted for both
    start_sched1 = schedule1.get('start_schedule') or schedule1.get('startSchedule')
    start_sched2 = schedule2.get('start_schedule') or schedule2.get('startSchedule')
    assert start_sched1 is not None, "Expected first profile chargingSchedule.startSchedule to not be omitted"
    assert start_sched2 is not None, "Expected second profile chargingSchedule.startSchedule to not be omitted"

    # stackLevel must be present and equal for both
    stack1 = profile1.get('stack_level') or profile1.get('stackLevel')
    stack2 = profile2.get('stack_level') or profile2.get('stackLevel')
    assert stack1 is not None, "Expected first profile stackLevel to be present"
    assert stack1 == stack2, f"Expected equal stackLevel for both profiles, got {stack1} and {stack2}"

    # chargingProfilePurpose must be equal for both and TxDefaultProfile or ChargingStationMaxProfile
    purpose1 = profile1.get('charging_profile_purpose') or profile1.get('chargingProfilePurpose')
    purpose2 = profile2.get('charging_profile_purpose') or profile2.get('chargingProfilePurpose')
    assert purpose1 == purpose2, f"Expected equal purpose for both profiles, got {purpose1} and {purpose2}"
    valid_purposes = (
        'TxDefaultProfile', 'ChargingStationMaxProfile',
        ChargingProfilePurposeEnumType.tx_default_profile,
        ChargingProfilePurposeEnumType.charging_station_max_profile,
    )
    assert purpose1 in valid_purposes, \
        f"Expected purpose TxDefaultProfile or ChargingStationMaxProfile, got {purpose1}"

    # chargingProfileKind must be equal for both
    kind1 = profile1.get('charging_profile_kind') or profile1.get('chargingProfileKind')
    kind2 = profile2.get('charging_profile_kind') or profile2.get('chargingProfileKind')
    assert kind1 == kind2, f"Expected equal kind for both profiles, got {kind1} and {kind2}"

    # If ChargingStationMaxProfile then kind must be Absolute
    if purpose1 in ('ChargingStationMaxProfile', ChargingProfilePurposeEnumType.charging_station_max_profile):
        assert kind1 in ('Absolute', ChargingProfileKindEnumType.absolute), \
            f"ChargingStationMaxProfile requires kind=Absolute, got {kind1}"

    # If TxDefaultProfile then kind must be Absolute or Recurring
    if purpose1 in ('TxDefaultProfile', ChargingProfilePurposeEnumType.tx_default_profile):
        assert kind1 in ('Absolute', 'Recurring', ChargingProfileKindEnumType.absolute, ChargingProfileKindEnumType.recurring), \
            f"TxDefaultProfile requires kind=Absolute or Recurring, got {kind1}"

    # If kind is Recurring then recurrencyKind must NOT be omitted, else omitted
    if kind1 in ('Recurring', ChargingProfileKindEnumType.recurring):
        recurrency1 = profile1.get('recurrency_kind') or profile1.get('recurrencyKind')
        assert recurrency1 is not None, "Expected recurrencyKind to not be omitted when kind is Recurring"
    else:
        recurrency1 = profile1.get('recurrency_kind') if profile1.get('recurrency_kind') is not None else profile1.get('recurrencyKind')
        assert recurrency1 is None, \
            f"Expected recurrencyKind to be omitted when kind is not Recurring, got {recurrency1}"

    logging.info("TC_K_04 completed successfully")
    start_task.cancel()
    await ws.close()
