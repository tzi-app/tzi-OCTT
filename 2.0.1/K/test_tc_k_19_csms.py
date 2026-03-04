"""
TC_K_19 - Set Charging Profile - ChargingProfileKind is Recurring
Use case: K01 | Requirements: N/a
System under test: CSMS

Description:
    To verify if the CSMS is able to send a Profile with a recurrencyKind specified as described at the OCPP
    specification.

Main:
    1. The CSMS sends a SetChargingProfileRequest
    2. The OCTT responds with a SetChargingProfileResponse with status Accepted

Tool validations:
    * Step 1: Message SetChargingProfileRequest
      - evseId <Configured evseId> AND
      - chargingProfile.stackLevel <Configured stackLevel> AND
      - chargingProfile.chargingProfilePurpose TxDefaultProfile AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
      - chargingProfile.chargingProfileKind Recurring AND
      - chargingProfile.recurrencyKind <Configured recurrencyKind>
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
    RecurrencyKindEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


class SmartChargingMockCP(TziChargePoint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._received_set_charging_profile = asyncio.Event()
        self._set_charging_profile_data = None

    @on(Action.set_charging_profile)
    async def on_set_charging_profile(self, evse_id, charging_profile, **kwargs):
        logging.info(f"Received SetChargingProfileRequest: evse_id={evse_id}")
        self._set_charging_profile_data = {
            'evse_id': evse_id,
            'charging_profile': charging_profile,
        }
        self._received_set_charging_profile.set()
        return call_result.SetChargingProfile(
            status=ChargingProfileStatusEnumType.accepted
        )


@pytest.mark.asyncio
async def test_tc_k_19():
    """Set Charging Profile - ChargingProfileKind is Recurring."""
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

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    await asyncio.wait_for(
        cp._received_set_charging_profile.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._set_charging_profile_data is not None
    req_data = cp._set_charging_profile_data
    profile = req_data['charging_profile']

    # evseId must be configured evseId
    assert req_data['evse_id'] == EVSE_ID, \
        f"Expected evseId={EVSE_ID}, got {req_data['evse_id']}"

    # chargingProfilePurpose must be TxDefaultProfile
    purpose = profile.get('charging_profile_purpose') or profile.get('chargingProfilePurpose')
    assert purpose in ('TxDefaultProfile', ChargingProfilePurposeEnumType.tx_default_profile), \
        f"Expected purpose=TxDefaultProfile, got {purpose}"

    # chargingProfileKind must be Recurring
    kind = profile.get('charging_profile_kind') or profile.get('chargingProfileKind')
    assert kind in ('Recurring', ChargingProfileKindEnumType.recurring), \
        f"Expected kind=Recurring, got {kind}"

    # recurrencyKind must be present
    recurrency = profile.get('recurrency_kind') or profile.get('recurrencyKind')
    assert recurrency is not None, "recurrencyKind must be present"
    assert recurrency in ('Daily', 'Weekly', RecurrencyKindEnumType.daily, RecurrencyKindEnumType.weekly), \
        f"Expected recurrencyKind=Daily or Weekly, got {recurrency}"

    # stackLevel must be present
    stack_level = profile.get('stack_level') or profile.get('stackLevel')
    assert stack_level is not None, "stackLevel must be present"

    # chargingSchedulePeriod startPeriod=0
    schedules = profile.get('charging_schedule') or profile.get('chargingSchedule')
    assert schedules is not None and len(schedules) > 0
    schedule = schedules[0] if isinstance(schedules, list) else schedules
    periods = schedule.get('charging_schedule_period') or schedule.get('chargingSchedulePeriod')
    assert periods is not None and len(periods) > 0
    period = periods[0]
    start_period = period.get('start_period') if period.get('start_period') is not None else period.get('startPeriod')
    assert start_period == 0, f"Expected startPeriod=0, got {start_period}"

    logging.info("TC_K_19 completed successfully")
    start_task.cancel()
    await ws.close()
