"""
TC_K_70 - Set Charging Profile - Multiple Profiles
Use case: n/a | Requirements: n/a
System under test: CSMS

Description:
    To verify if the CSMS is able to set multiple Charging Profiles.

Before:
    Reusable State: EnergyTransferStarted

Main:
    1. The CSMS sends a SetChargingProfileRequest (TxDefaultProfile)
    2. The OCTT responds with a SetChargingProfileResponse with status Accepted
    3. The CSMS sends a SetChargingProfileRequest (ChargingStationMaxProfile, different id)
    4. The OCTT responds with a SetChargingProfileResponse with status Accepted

Tool validations:
    * Step 1: purpose TxDefaultProfile, kind Absolute or Recurring, startSchedule not omitted
    * Step 3: different profile id, purpose ChargingStationMaxProfile, kind Absolute, startSchedule not omitted
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
from utils import get_basic_auth_headers, generate_transaction_id, now_iso
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
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
        logging.info(f"Received SetChargingProfileRequest #{self._set_charging_profile_count + 1}")
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
async def test_tc_k_70():
    """Set Charging Profile - Multiple Profiles."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
    )
    time.sleep(0.5)

    cp = SmartChargingMockCP(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    transaction_id = generate_transaction_id()

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Before: Execute Reusable State EnergyTransferStarted
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Wait for both SetChargingProfileRequests
    await asyncio.wait_for(
        cp._all_profiles_received.wait(),
        timeout=CSMS_ACTION_TIMEOUT * 2,
    )

    assert len(cp._set_charging_profile_requests) >= 2

    # Validate both profiles against tool validation requirements
    profile1 = cp._set_charging_profile_requests[0]['charging_profile']
    profile2 = cp._set_charging_profile_requests[1]['charging_profile']

    id1 = profile1.get('id')
    id2 = profile2.get('id')
    stack1 = profile1.get('stack_level') or profile1.get('stackLevel')
    stack2 = profile2.get('stack_level') or profile2.get('stackLevel')
    purpose1 = profile1.get('charging_profile_purpose') or profile1.get('chargingProfilePurpose')
    purpose2 = profile2.get('charging_profile_purpose') or profile2.get('chargingProfilePurpose')
    kind1 = profile1.get('charging_profile_kind') or profile1.get('chargingProfileKind')
    kind2 = profile2.get('charging_profile_kind') or profile2.get('chargingProfileKind')

    schedules1 = profile1.get('charging_schedule') or profile1.get('chargingSchedule')
    schedules2 = profile2.get('charging_schedule') or profile2.get('chargingSchedule')
    schedule1 = schedules1[0] if isinstance(schedules1, list) and schedules1 else schedules1
    schedule2 = schedules2[0] if isinstance(schedules2, list) and schedules2 else schedules2
    assert schedule1 is not None, "Expected first profile chargingSchedule to be present"
    assert schedule2 is not None, "Expected second profile chargingSchedule to be present"
    start_schedule1 = schedule1.get('start_schedule') or schedule1.get('startSchedule')
    start_schedule2 = schedule2.get('start_schedule') or schedule2.get('startSchedule')
    recurrency1 = profile1.get('recurrency_kind') or profile1.get('recurrencyKind')

    assert purpose1 in ('TxDefaultProfile', ChargingProfilePurposeEnumType.tx_default_profile), \
        f"Expected first purpose=TxDefaultProfile, got {purpose1}"
    assert kind1 in ('Absolute', 'Recurring', ChargingProfileKindEnumType.absolute, ChargingProfileKindEnumType.recurring), \
        f"Expected first kind=Absolute or Recurring, got {kind1}"
    assert start_schedule1 is not None, "Expected first profile chargingSchedule.startSchedule to be present"
    if kind1 in ('Recurring', ChargingProfileKindEnumType.recurring):
        assert recurrency1 is not None, "Expected first profile recurrencyKind when chargingProfileKind is Recurring"

    assert id1 is not None and id2 is not None and id1 != id2, \
        f"Expected different chargingProfile.id values, got {id1} and {id2}"
    assert purpose2 in ('ChargingStationMaxProfile', ChargingProfilePurposeEnumType.charging_station_max_profile), \
        f"Expected second purpose=ChargingStationMaxProfile, got {purpose2}"
    assert kind2 in ('Absolute', ChargingProfileKindEnumType.absolute), \
        f"Expected second kind=Absolute, got {kind2}"
    assert start_schedule2 is not None, "Expected second profile chargingSchedule.startSchedule to be present"

    # K01.FR.31 compliance: startPeriod of first chargingSchedulePeriod SHALL always be 0
    # (The received Charging Profiles must comply with the requirements defined at part 2 specification)
    for idx, schedule in enumerate([schedule1, schedule2], 1):
        periods = schedule.get('charging_schedule_period') or schedule.get('chargingSchedulePeriod')
        assert periods is not None and len(periods) > 0, \
            f"Profile {idx}: chargingSchedulePeriod must be present"
        first_period = periods[0]
        start_period = first_period.get('start_period') if first_period.get('start_period') is not None else first_period.get('startPeriod')
        assert start_period == 0, \
            f"K01.FR.31: Profile {idx} expected startPeriod=0, got {start_period}"

    logging.info("TC_K_70 completed successfully")
    start_task.cancel()
    await ws.close()
