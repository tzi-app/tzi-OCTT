"""
TC_K_15 - Set Charging Profile - Not Supported
Use case: K01 | Requirements: N/a
System under test: CSMS

Description:
    To verify if the CSMS is able to send a Profile, while the charging station does not support
    chargingprofiles, and read the response as described at the OCPP specification.

Main:
    1. The CSMS sends a SetChargingProfileRequest
    2. The OCTT responds with RPC Framework: CALLERROR: NotSupported.

Tool validations:
    * Step 1: Message SetChargingProfileRequest
      - evseId <Configured evseId> AND
      - chargingProfile.stackLevel <Configured stackLevel> AND
      - chargingProfile.chargingProfilePurpose TxDefaultProfile AND
      - chargingProfile.chargingProfileKind Absolute AND
      - chargingProfile.chargingSchedule.startSchedule <Not omitted> AND
      - chargingProfile.chargingSchedule.chargingRateUnit <Configured ChargingRateUnit> AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
      - chargingProfile.chargingSchedule.duration <Configured duration> AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 6.0 or 6000.0 AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.numberPhases <Configured numberPhases>

Note: This test requires the mock CP to respond with a CALLERROR NotSupported. Since the ocpp library
handles this as an exception, the handler raises an error that maps to NotSupported.
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
from ocpp.v201.enums import (
    Action,
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    ChargingProfilePurposeEnumType,
    ChargingProfileKindEnumType,
)
from ocpp.exceptions import NotSupportedError

from tzi_charge_point import TziChargePoint
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

    @on(Action.set_charging_profile)
    async def on_set_charging_profile(self, evse_id, charging_profile, **kwargs):
        logging.info(f"Received SetChargingProfileRequest: evse_id={evse_id}")
        self._set_charging_profile_data = {
            'evse_id': evse_id,
            'charging_profile': charging_profile,
        }
        self._received_set_charging_profile.set()
        raise NotSupportedError(
            description="Charging profiles not supported by this Charging Station"
        )


@pytest.mark.asyncio
async def test_tc_k_15():
    """Set Charging Profile - Not Supported."""
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

    # Wait for CSMS to send SetChargingProfileRequest
    await asyncio.wait_for(
        cp._received_set_charging_profile.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate the request was received (response was CALLERROR NotSupported)
    assert cp._set_charging_profile_data is not None
    req_data = cp._set_charging_profile_data
    profile = req_data['charging_profile']

    # Validate evseId
    assert req_data['evse_id'] == EVSE_ID, \
        f"Expected evseId={EVSE_ID}, got {req_data['evse_id']}"

    # Validate purpose is TxDefaultProfile
    purpose = profile.get('charging_profile_purpose') or profile.get('chargingProfilePurpose')
    assert purpose in ('TxDefaultProfile', ChargingProfilePurposeEnumType.tx_default_profile), \
        f"Expected purpose=TxDefaultProfile, got {purpose}"

    # Validate kind is Absolute
    kind = profile.get('charging_profile_kind') or profile.get('chargingProfileKind')
    assert kind in ('Absolute', ChargingProfileKindEnumType.absolute), \
        f"Expected kind=Absolute, got {kind}"

    # stackLevel must be present
    stack_level = profile.get('stack_level') or profile.get('stackLevel')
    assert stack_level is not None, "stackLevel must be present"

    # chargingSchedule validations
    schedules = profile.get('charging_schedule') or profile.get('chargingSchedule')
    assert schedules is not None and len(schedules) > 0, "chargingSchedule must be present"
    schedule = schedules[0] if isinstance(schedules, list) else schedules

    # startSchedule must NOT be omitted
    start_schedule = schedule.get('start_schedule') or schedule.get('startSchedule')
    assert start_schedule is not None, "startSchedule must not be omitted"

    # chargingRateUnit must be present
    rate_unit = schedule.get('charging_rate_unit') or schedule.get('chargingRateUnit')
    assert rate_unit is not None, "chargingRateUnit must be present"

    # duration must be present
    duration = schedule.get('duration')
    assert duration is not None, "duration must be present"

    # chargingSchedulePeriod validations
    periods = schedule.get('charging_schedule_period') or schedule.get('chargingSchedulePeriod')
    assert periods is not None and len(periods) > 0, "chargingSchedulePeriod must be present"
    period = periods[0]

    # startPeriod must be 0
    start_period = period.get('start_period') if period.get('start_period') is not None else period.get('startPeriod')
    assert start_period == 0, f"Expected startPeriod=0, got {start_period}"

    # limit must be 6.0 or 6000.0
    limit = period.get('limit')
    assert limit in (6.0, 6000.0), f"Expected limit=6.0 or 6000.0, got {limit}"

    # numberPhases validation
    number_phases = period.get('number_phases') if period.get('number_phases') is not None else period.get('numberPhases')
    if CONFIGURED_NUMBER_PHASES != 3:
        assert number_phases == CONFIGURED_NUMBER_PHASES, \
            f"Expected numberPhases={CONFIGURED_NUMBER_PHASES}, got {number_phases}"
    else:
        assert number_phases is None or number_phases == 3, \
            f"Expected numberPhases=3 or omitted, got {number_phases}"

    logging.info("TC_K_15 completed successfully")
    start_task.cancel()
    await ws.close()
