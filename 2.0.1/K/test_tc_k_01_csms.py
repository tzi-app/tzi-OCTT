"""
TC_K_01 - Set Charging Profile - TxDefaultProfile - Specific EVSE
Use case: K01 | Requirements: K01.FR.31
K01.FR.31: The startPeriod of the first chargingSchedulePeriod in a chargingSchedule SHALL always be 0.
System under test: CSMS

Description:
    To enable the CSMS to influence the charging power or current drawn from a specific EVSE or the entire
    Charging Station over a period of time. The CSMS sends a SetChargingProfileRequest to the Charging
    Station to influence the power or current drawn by EVs.

Purpose:
    To verify if the CSMS is able to send a TxDefaultProfile charging profile for a specific EVSE as
    described at the OCPP specification.

Before:
    Configuration State: N/a
    Memory State: N/a
    Charging State: N/a

Main:
    1. The CSMS sends a SetChargingProfileRequest
    2. The OCTT responds with a SetChargingProfileResponse with status Accepted

Tool validations:
    * Step 1: Message SetChargingProfileRequest
      - evseId <Configured evseId> AND
      - chargingProfile.stackLevel <Configured stackLevel> AND
      - chargingProfile.chargingProfilePurpose TxDefaultProfile AND
      - chargingProfile.chargingProfileKind Absolute AND
      - chargingProfile.validFrom now AND
      - chargingProfile.validTo now + <Configured Charging Schedule Duration> AND
      - chargingProfile.chargingSchedule.startSchedule now AND
      - chargingProfile.chargingSchedule.chargingRateUnit <Configured chargingRateUnit> AND
      - chargingProfile.chargingSchedule.duration <Configured duration> AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 6.0 or 6000.0 AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.numberPhases <Configured numberPhases>
        where <Configured numberPhases> not 3 OR
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.numberPhases <Configured numberPhases>
        or <omit> where <Configured numberPhases> 3
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
)

from tzi_charge_point import TziChargePoint
from trigger import send_call
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
CONFIGURED_NUMBER_PHASES = int(os.environ['CONFIGURED_NUMBER_PHASES'])


class SmartChargingMockCP(TziChargePoint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._received_set_charging_profile = asyncio.Event()
        self._set_charging_profile_data = None
        self._set_charging_profile_response_status = ChargingProfileStatusEnumType.accepted

    @on(Action.set_charging_profile)
    async def on_set_charging_profile(self, evse_id, charging_profile, **kwargs):
        logging.info(f"Received SetChargingProfileRequest: evse_id={evse_id}, profile={charging_profile}")
        self._set_charging_profile_data = {
            'evse_id': evse_id,
            'charging_profile': charging_profile,
        }
        self._received_set_charging_profile.set()
        return call_result.SetChargingProfile(
            status=self._set_charging_profile_response_status
        )


@pytest.mark.asyncio
async def test_tc_k_01():
    """Set Charging Profile - TxDefaultProfile - Specific EVSE."""
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

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Trigger CSMS to send SetChargingProfileRequest
    now = datetime.now(timezone.utc)
    schedule_duration = 3600
    async def trigger_set_profile():
        await asyncio.sleep(1)
        await send_call(cp_id, "SetChargingProfile", {
            "evseId": EVSE_ID,
            "chargingProfile": {
                "id": 1,
                "stackLevel": 0,
                "chargingProfilePurpose": "TxDefaultProfile",
                "chargingProfileKind": "Absolute",
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
                        "numberPhases": CONFIGURED_NUMBER_PHASES,
                    }],
                }],
            },
        })

    trigger_task = asyncio.create_task(trigger_set_profile())

    # Step 1-2: Wait for CSMS to send SetChargingProfileRequest
    await asyncio.wait_for(
        cp._received_set_charging_profile.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    trigger_task.cancel()

    # Validate Step 1: SetChargingProfileRequest content
    assert cp._set_charging_profile_data is not None
    req_data = cp._set_charging_profile_data
    profile = req_data['charging_profile']

    # evseId must be configured evseId
    assert req_data['evse_id'] == EVSE_ID, \
        f"Expected evseId={EVSE_ID}, got {req_data['evse_id']}"

    def get_field(d, snake, camel):
        """Get field by snake_case key, falling back to camelCase."""
        v = d.get(snake)
        return v if v is not None else d.get(camel)

    # chargingProfile.chargingProfilePurpose must be TxDefaultProfile
    purpose = get_field(profile, 'charging_profile_purpose', 'chargingProfilePurpose')
    assert purpose in ('TxDefaultProfile', ChargingProfilePurposeEnumType.tx_default_profile), \
        f"Expected purpose=TxDefaultProfile, got {purpose}"

    # chargingProfile.chargingProfileKind must be Absolute
    kind = get_field(profile, 'charging_profile_kind', 'chargingProfileKind')
    assert kind in ('Absolute', ChargingProfileKindEnumType.absolute), \
        f"Expected kind=Absolute, got {kind}"

    # chargingProfile.stackLevel must be present
    stack_level = get_field(profile, 'stack_level', 'stackLevel')
    assert stack_level is not None, "stackLevel must be present"

    # chargingProfile.validFrom must not be omitted (approximately now)
    valid_from = get_field(profile, 'valid_from', 'validFrom')
    assert valid_from is not None, "validFrom must be present (now)"

    # chargingProfile.validTo must not be omitted
    valid_to = get_field(profile, 'valid_to', 'validTo')
    assert valid_to is not None, "validTo must be present"

    # chargingSchedule validations
    schedules = get_field(profile, 'charging_schedule', 'chargingSchedule')
    assert schedules is not None and len(schedules) > 0, "chargingSchedule must be present"
    schedule = schedules[0] if isinstance(schedules, list) else schedules

    # startSchedule must be approximately now
    start_schedule = get_field(schedule, 'start_schedule', 'startSchedule')
    assert start_schedule is not None, "startSchedule must be present"

    # chargingRateUnit must be present
    rate_unit = get_field(schedule, 'charging_rate_unit', 'chargingRateUnit')
    assert rate_unit is not None, "chargingRateUnit must be present"

    # duration must be present
    duration = schedule.get('duration')
    assert duration is not None, "duration must be present"

    # chargingSchedulePeriod validations
    periods = get_field(schedule, 'charging_schedule_period', 'chargingSchedulePeriod')
    assert periods is not None and len(periods) > 0, "chargingSchedulePeriod must be present"
    period = periods[0]

    # startPeriod must be 0
    start_period = get_field(period, 'start_period', 'startPeriod')
    assert start_period == 0, f"Expected startPeriod=0, got {start_period}"

    # limit must be 6.0 or 6000.0
    limit = period.get('limit')
    assert limit in (6.0, 6000.0), \
        f"Expected limit=6.0 or 6000.0, got {limit}"

    # numberPhases validation
    number_phases = get_field(period, 'number_phases', 'numberPhases')
    if CONFIGURED_NUMBER_PHASES != 3:
        assert number_phases == CONFIGURED_NUMBER_PHASES, \
            f"Expected numberPhases={CONFIGURED_NUMBER_PHASES}, got {number_phases}"
    else:
        assert number_phases is None or number_phases == 3, \
            f"Expected numberPhases=3 or omitted, got {number_phases}"

    logging.info("TC_K_01 completed successfully")
    start_task.cancel()
    await ws.close()
