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
from datetime import datetime, timedelta, timezone

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
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context
from trigger import send_call

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

    # Trigger CSMS to send SetChargingProfileRequest
    now = datetime.now(timezone.utc)
    schedule_duration = 86400

    async def trigger_action():
        await asyncio.sleep(1)
        await send_call(cp_id, "SetChargingProfile", {
            "evseId": EVSE_ID,
            "chargingProfile": {
                "id": 1,
                "stackLevel": 0,
                "chargingProfilePurpose": "TxDefaultProfile",
                "chargingProfileKind": "Recurring",
                "recurrencyKind": "Daily",
                "validFrom": now.isoformat(),
                "validTo": (now + timedelta(seconds=schedule_duration)).isoformat(),
                "chargingSchedule": [{
                    "id": 1,
                    "startSchedule": now.isoformat(),
                    "chargingRateUnit": "A",
                    "duration": schedule_duration,
                    "chargingSchedulePeriod": [{
                        "startPeriod": 0,
                        "limit": 6.0,
                    }],
                }],
            },
        })
    trigger_task = asyncio.create_task(trigger_action())

    await asyncio.wait_for(
        cp._received_set_charging_profile.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    assert cp._set_charging_profile_data is not None
    req_data = cp._set_charging_profile_data
    profile = req_data['charging_profile']

    def get_field(d, snake, camel):
        """Get field by snake_case key, falling back to camelCase."""
        v = d.get(snake)
        return v if v is not None else d.get(camel)

    # evseId must be configured evseId
    assert req_data['evse_id'] == EVSE_ID, \
        f"Expected evseId={EVSE_ID}, got {req_data['evse_id']}"

    # chargingProfilePurpose must be TxDefaultProfile
    purpose = get_field(profile, 'charging_profile_purpose', 'chargingProfilePurpose')
    assert purpose in ('TxDefaultProfile', ChargingProfilePurposeEnumType.tx_default_profile), \
        f"Expected purpose=TxDefaultProfile, got {purpose}"

    # chargingProfileKind must be Recurring
    kind = get_field(profile, 'charging_profile_kind', 'chargingProfileKind')
    assert kind in ('Recurring', ChargingProfileKindEnumType.recurring), \
        f"Expected kind=Recurring, got {kind}"

    # recurrencyKind must be present
    recurrency = get_field(profile, 'recurrency_kind', 'recurrencyKind')
    assert recurrency is not None, "recurrencyKind must be present"
    assert recurrency in ('Daily', 'Weekly', RecurrencyKindEnumType.daily, RecurrencyKindEnumType.weekly), \
        f"Expected recurrencyKind=Daily or Weekly, got {recurrency}"

    # stackLevel must be present
    stack_level = get_field(profile, 'stack_level', 'stackLevel')
    assert stack_level is not None, "stackLevel must be present"

    # chargingSchedulePeriod startPeriod=0
    schedules = get_field(profile, 'charging_schedule', 'chargingSchedule')
    assert schedules is not None and len(schedules) > 0
    schedule = schedules[0] if isinstance(schedules, list) else schedules
    periods = get_field(schedule, 'charging_schedule_period', 'chargingSchedulePeriod')
    assert periods is not None and len(periods) > 0
    period = periods[0]
    start_period = get_field(period, 'start_period', 'startPeriod')
    assert start_period == 0, f"Expected startPeriod=0, got {start_period}"

    logging.info("TC_K_19 completed successfully")
    start_task.cancel()
    await ws.close()
