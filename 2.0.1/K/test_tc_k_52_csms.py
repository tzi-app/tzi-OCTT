"""
TC_K_52 - Set / Update External Charging Limit - ChargingStationExternalConstraints in report
Use case: K12 | Requirements: N/a
System under test: CSMS

Description:
    To verify if the CSMS is able to correctly receive the report when a charging limit has been externally
    changed in a charging station as described at the OCPP specification.

Main:
    1. The CSMS sends a GetChargingProfilesRequest
    2. The OCTT responds with a GetChargingProfilesResponse with status Accepted
    3. The OCTT sends a ReportChargingProfilesRequest with
       requestId Generated Id AND
       chargingProfile.chargingProfilePurpose ChargingStationExternalConstraints
    4. The CSMS responds with a ReportChargingProfilesResponse
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
from ocpp.v201 import call, call_result
from ocpp.v201.enums import (
    Action,
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    GetChargingProfileStatusEnumType,
    ChargingLimitSourceEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, now_iso, build_default_ssl_context

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
        self._received_get_charging_profiles = asyncio.Event()
        self._get_charging_profiles_data = None

    @on(Action.get_charging_profiles)
    async def on_get_charging_profiles(self, request_id, charging_profile, evse_id=None, **kwargs):
        logging.info(f"Received GetChargingProfilesRequest: request_id={request_id}")
        self._get_charging_profiles_data = {
            'request_id': request_id,
            'charging_profile': charging_profile,
            'evse_id': evse_id,
        }
        self._received_get_charging_profiles.set()
        return call_result.GetChargingProfiles(
            status=GetChargingProfileStatusEnumType.accepted
        )


@pytest.mark.asyncio
async def test_tc_k_52():
    """External Charging Limit - ChargingStationExternalConstraints in report."""
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

    # First: CS sends NotifyChargingLimitRequest to establish external limit
    notify_payload = call.NotifyChargingLimit(
        charging_limit={
            'charging_limit_source': ChargingLimitSourceEnumType.ems,
        },
    )
    await cp.call(notify_payload)

    # Step 1-2: Wait for CSMS to send GetChargingProfilesRequest
    await asyncio.wait_for(
        cp._received_get_charging_profiles.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_charging_profiles_data is not None
    request_id = cp._get_charging_profiles_data['request_id']

    # Step 3: Send ReportChargingProfilesRequest with ChargingStationExternalConstraints
    report_payload = call.ReportChargingProfiles(
        request_id=request_id,
        charging_limit_source=ChargingLimitSourceEnumType.ems,
        charging_profile=[{
            'id': 1,
            'stack_level': 0,
            'charging_profile_purpose': 'ChargingStationExternalConstraints',
            'charging_profile_kind': 'Absolute',
            'charging_schedule': [{
                'id': 1,
                'charging_rate_unit': 'A',
                'charging_schedule_period': [{'start_period': 0, 'limit': 16.0}],
            }],
        }],
        evse_id=EVSE_ID,
    )
    # Step 4: CSMS responds with ReportChargingProfilesResponse
    await cp.call(report_payload)

    logging.info("TC_K_52 completed successfully")
    start_task.cancel()
    await ws.close()
