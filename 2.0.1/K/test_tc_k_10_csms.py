"""
TC_K_10 - Set Charging Profile - TxDefaultProfile - All EVSE
Use case: K01 | Requirements: K01.FR.31
K01.FR.31: The startPeriod of the first chargingSchedulePeriod in a chargingSchedule SHALL always be 0.
System under test: CSMS

Description:
    To enable the CSMS to influence the charging power or current drawn from a specific EVSE or the entire
    Charging Station over a period of time.

Purpose:
    To verify if the CSMS is able to send a TxDefaultProfile charging profile for all EVSE as described at
    the OCPP specification.

Main:
    1. The CSMS sends a SetChargingProfileRequest - chargingProfile.id <Configured chargingProfileId>
    2. The OCTT responds with a SetChargingProfileResponse with status Accepted

Tool validations:
    * Step 1: Message SetChargingProfileRequest
      - evseId 0 AND
      - chargingProfile.stackLevel <Configured stackLevel> AND
      - chargingProfile.chargingProfilePurpose TxDefaultProfile AND
      - chargingProfile.chargingProfileKind Absolute AND
      - chargingProfile.validFrom <Not omitted> AND
      - chargingProfile.validTo <Not omitted> AND
      - chargingProfile.chargingSchedule.startSchedule <Not omitted> AND
      - chargingProfile.chargingSchedule.chargingRateUnit <Configured ChargingRateUnit> AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
      - chargingProfile.chargingSchedule.duration <Configured duration> AND
      - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 6.0 or 6000.0
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
from utils import get_basic_auth_headers, now_iso

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
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
        return call_result.SetChargingProfile(
            status=ChargingProfileStatusEnumType.accepted
        )


@pytest.mark.asyncio
async def test_tc_k_10():
    """Set Charging Profile - TxDefaultProfile - All EVSE."""
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

    # evseId must be 0 (all EVSE)
    assert req_data['evse_id'] == 0, \
        f"Expected evseId=0, got {req_data['evse_id']}"

    # chargingProfilePurpose must be TxDefaultProfile
    purpose = profile.get('charging_profile_purpose') or profile.get('chargingProfilePurpose')
    assert purpose in ('TxDefaultProfile', ChargingProfilePurposeEnumType.tx_default_profile), \
        f"Expected purpose=TxDefaultProfile, got {purpose}"

    # chargingProfileKind must be Absolute
    kind = profile.get('charging_profile_kind') or profile.get('chargingProfileKind')
    assert kind in ('Absolute', ChargingProfileKindEnumType.absolute), \
        f"Expected kind=Absolute, got {kind}"

    # stackLevel must be present
    stack_level = profile.get('stack_level') or profile.get('stackLevel')
    assert stack_level is not None, "stackLevel must be present"

    # validFrom must not be omitted
    valid_from = profile.get('valid_from') or profile.get('validFrom')
    assert valid_from is not None, "validFrom must not be omitted"

    # validTo must not be omitted
    valid_to = profile.get('valid_to') or profile.get('validTo')
    assert valid_to is not None, "validTo must not be omitted"

    # chargingSchedule validations
    schedules = profile.get('charging_schedule') or profile.get('chargingSchedule')
    assert schedules is not None and len(schedules) > 0
    schedule = schedules[0] if isinstance(schedules, list) else schedules

    start_schedule = schedule.get('start_schedule') or schedule.get('startSchedule')
    assert start_schedule is not None, "startSchedule must not be omitted"

    rate_unit = schedule.get('charging_rate_unit') or schedule.get('chargingRateUnit')
    assert rate_unit is not None, "chargingRateUnit must be present"

    duration = schedule.get('duration')
    assert duration is not None, "duration must be present"

    periods = schedule.get('charging_schedule_period') or schedule.get('chargingSchedulePeriod')
    assert periods is not None and len(periods) > 0
    period = periods[0]

    start_period = period.get('start_period') if period.get('start_period') is not None else period.get('startPeriod')
    assert start_period == 0, f"Expected startPeriod=0, got {start_period}"

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

    logging.info("TC_K_10 completed successfully")
    start_task.cancel()
    await ws.close()
