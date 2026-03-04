"""
TC_K_43 - Get Composite Schedule - Specific EVSE
Use case: K08 | Requirements: K08.FR.01
K08.FR.01: The CSMS MAY request the Charging Station to report the CompositeSchedule by sending GetCompositeScheduleRequest.
System under test: CSMS

Description:
    The CSMS requests a composite schedule which is a combination of local limits and the prevailing
    Charging Profiles of the different chargingProfilePurposes and stack levels.

Purpose:
    To verify if the CSMS is able to calculate request a composite schedule from the Charging Station for a
    specific EVSE.

Main:
    1. The CSMS sends a GetCompositeScheduleRequest
    2. The OCTT responds with a GetCompositeScheduleResponse
       With status Accepted, schedule.evseId 1, schedule.duration 300,
       schedule.chargingRateUnit <from step 1>,
       schedule.chargingSchedulePeriod[0].startPeriod 0,
       schedule.chargingSchedulePeriod[0].limit 10

Tool validations:
    * Step 1: (Message: GetCompositeScheduleRequest)
      - evseId 1
      - duration is <Configured duration>
      - chargingRateUnit <Configured chargingRateUnit>
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
    GenericStatusEnumType,
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
        self._received_get_composite_schedule = asyncio.Event()
        self._get_composite_schedule_data = None

    @on(Action.get_composite_schedule)
    async def on_get_composite_schedule(self, duration, evse_id, charging_rate_unit=None, **kwargs):
        logging.info(f"Received GetCompositeScheduleRequest: duration={duration}, evse_id={evse_id}, "
                     f"charging_rate_unit={charging_rate_unit}")
        self._get_composite_schedule_data = {
            'duration': duration,
            'evse_id': evse_id,
            'charging_rate_unit': charging_rate_unit,
        }
        self._received_get_composite_schedule.set()

        rate_unit = charging_rate_unit if charging_rate_unit else 'A'
        # Note: Multiply limit by 1000 if chargingRateUnit is W (spec: limit 10 means 10A or 10kW=10000W)
        limit = 10000.0 if rate_unit == 'W' else 10.0

        return call_result.GetCompositeSchedule(
            status=GenericStatusEnumType.accepted,
            schedule={
                'evse_id': 1,
                'duration': 300,
                'schedule_start': now_iso(),
                'charging_rate_unit': rate_unit,
                'charging_schedule_period': [
                    {'start_period': 0, 'limit': limit},
                ],
            }
        )


@pytest.mark.asyncio
async def test_tc_k_43():
    """Get Composite Schedule - Specific EVSE."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ssl_ctx = build_default_ssl_context() if CSMS_ADDRESS.startswith('wss://') else None
    ws = await websockets.connect(uri=uri, subprotocols=['ocpp2.0.1'], extra_headers=headers)
    time.sleep(0.5)

    cp = SmartChargingMockCP(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted
    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    await asyncio.wait_for(cp._received_get_composite_schedule.wait(), timeout=CSMS_ACTION_TIMEOUT)

    assert cp._get_composite_schedule_data is not None
    req_data = cp._get_composite_schedule_data

    # evseId must be 1
    assert req_data['evse_id'] == 1, f"Expected evseId=1, got {req_data['evse_id']}"

    # duration must be present
    assert req_data['duration'] is not None, "duration must be present"

    # chargingRateUnit must be present
    assert req_data['charging_rate_unit'] is not None, "chargingRateUnit must be present"

    logging.info("TC_K_43 completed successfully")
    start_task.cancel()
    await ws.close()
