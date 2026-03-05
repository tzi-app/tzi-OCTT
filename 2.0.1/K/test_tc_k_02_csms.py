"""
TC_K_02 - Set Charging Profile - TxProfile without ongoing transaction on the specified EVSE
Use case: K01 | Requirements: N/a
System under test: CSMS

Description:
    To enable the CSMS to influence the charging power or current drawn from a specific EVSE or the entire
    Charging Station over a period of time.

Purpose:
    To verify if the CSMS is able to send a TxProfile and read the charger's feedback while no transaction is
    ongoing for a specific EVSE as described at the OCPP specification.

Prerequisite:
    If the CSMS supports sending a TxProfile while there is no transaction ongoing.

Before:
    Configuration State: N/a
    Memory State: N/a
    Charging State: N/a

Main:
    1. The CSMS sends a SetChargingProfileRequest - chargingProfile.id <Configured chargingProfileId>
    2. The OCTT responds with a SetChargingProfileResponse with status Rejected

Tool validations:
    * Step 1: Message SetChargingProfileRequest
      - evseId <Configured evseId> AND
      - chargingProfile.chargingProfilePurpose TxProfile AND
      - chargingProfile.stackLevel <Configured stackLevel> AND
      - chargingProfile.chargingProfileKind Relative AND
      - chargingProfile.chargingSchedule.startSchedule must be omitted AND
      - chargingProfile.chargingSchedule.chargingRateUnit <Configured chargingRateUnit> AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 7.0 or 7000.0 AND
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
        self._set_charging_profile_response_status = ChargingProfileStatusEnumType.rejected

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
async def test_tc_k_02():
    """Set Charging Profile - TxProfile without ongoing transaction."""
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
    async def trigger_set_profile():
        await asyncio.sleep(1)
        await send_call(cp_id, "SetChargingProfile", {
            "evseId": EVSE_ID,
            "chargingProfile": {
                "id": 1,
                "stackLevel": 0,
                "chargingProfilePurpose": "TxProfile",
                "chargingProfileKind": "Relative",
                "chargingSchedule": [{
                    "id": 1,
                    "chargingRateUnit": "A",
                    "chargingSchedulePeriod": [{
                        "startPeriod": 0,
                        "limit": 7.0,
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

    # Validate Step 1
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

    # chargingProfilePurpose must be TxProfile
    purpose = get_field(profile, 'charging_profile_purpose', 'chargingProfilePurpose')
    assert purpose in ('TxProfile', ChargingProfilePurposeEnumType.tx_profile), \
        f"Expected purpose=TxProfile, got {purpose}"

    # stackLevel must be present
    stack_level = get_field(profile, 'stack_level', 'stackLevel')
    assert stack_level is not None, "stackLevel must be present"

    # chargingProfileKind must be Relative
    kind = get_field(profile, 'charging_profile_kind', 'chargingProfileKind')
    assert kind in ('Relative', ChargingProfileKindEnumType.relative), \
        f"Expected kind=Relative, got {kind}"

    # chargingSchedule validations
    schedules = get_field(profile, 'charging_schedule', 'chargingSchedule')
    assert schedules is not None and len(schedules) > 0
    schedule = schedules[0] if isinstance(schedules, list) else schedules

    # startSchedule must be omitted for Relative kind
    start_schedule = get_field(schedule, 'start_schedule', 'startSchedule')
    assert start_schedule is None, \
        f"Expected startSchedule to be omitted for Relative kind, got {start_schedule}"

    # chargingRateUnit must be present
    rate_unit = get_field(schedule, 'charging_rate_unit', 'chargingRateUnit')
    assert rate_unit is not None, "chargingRateUnit must be present"

    periods = get_field(schedule, 'charging_schedule_period', 'chargingSchedulePeriod')
    assert periods is not None and len(periods) > 0
    period = periods[0]

    start_period = get_field(period, 'start_period', 'startPeriod')
    assert start_period == 0, f"Expected startPeriod=0, got {start_period}"

    limit = period.get('limit')
    assert limit in (7.0, 7000.0), f"Expected limit=7.0 or 7000.0, got {limit}"

    # numberPhases validation
    number_phases = get_field(period, 'number_phases', 'numberPhases')
    if CONFIGURED_NUMBER_PHASES != 3:
        assert number_phases == CONFIGURED_NUMBER_PHASES, \
            f"Expected numberPhases={CONFIGURED_NUMBER_PHASES}, got {number_phases}"
    else:
        assert number_phases is None or number_phases == 3, \
            f"Expected numberPhases=3 or omitted, got {number_phases}"

    # Step 2: Response is Rejected (handled by handler above)

    logging.info("TC_K_02 completed successfully")
    start_task.cancel()
    await ws.close()
