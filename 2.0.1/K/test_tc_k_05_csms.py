"""
TC_K_05 - Clear Charging Profile - With chargingProfileId
Use case: K10 | Requirements: K10.FR.02
K10.FR.02: The CSMS SHALL either specify a chargingProfile.id OR include one or more of the fields stackLevel, evseId and chargingProfilePurpose in the ClearChargingProfileRequest to specify which Charging Profiles need to be cleared.
System under test: CSMS

Description:
    If the CSMS wishes to clear some or all of the charging profiles that were previously sent to the
    Charging Station, then the CSMS sends a ClearChargingProfileRequest to the Charging Station.

Purpose:
    To verify if the CSMS is able to request the charging station to clear a specific charging profile (not
    TxDefault) with only a chargingProfileId as described at the OCPP specification.

Before:
    Memory State:
      CSMS sends a GetChargingProfilesRequest
      OCTT responds with a GetChargingProfilesResponse with status Accepted
      OCTT sends a ReportChargingProfilesRequest
      CSMS responds with a ReportChargingProfilesResponse

Main:
    1. The CSMS sends a ClearChargingProfileRequest with
       chargingProfileId <Generated chargingProfileId> AND chargingProfileCriteria omit
    2. The OCTT responds with a ClearChargingProfileResponse with status Accepted

Tool validations:
    - N/a
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
    ClearChargingProfileStatusEnumType,
    GetChargingProfileStatusEnumType,
    ChargingLimitSourceEnumType,
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
        self._received_get_charging_profiles = asyncio.Event()
        self._get_charging_profiles_data = None
        self._received_clear_charging_profile = asyncio.Event()
        self._clear_charging_profile_data = None
        self._charging_profile_id = 100

    @on(Action.get_charging_profiles)
    async def on_get_charging_profiles(self, request_id, charging_profile, evse_id=None, **kwargs):
        logging.info(f"Received GetChargingProfilesRequest: request_id={request_id}, evse_id={evse_id}")
        self._get_charging_profiles_data = {
            'request_id': request_id,
            'charging_profile': charging_profile,
            'evse_id': evse_id,
        }
        self._received_get_charging_profiles.set()
        return call_result.GetChargingProfiles(
            status=GetChargingProfileStatusEnumType.accepted
        )

    @on(Action.clear_charging_profile)
    async def on_clear_charging_profile(self, charging_profile_id=None, charging_profile_criteria=None, **kwargs):
        logging.info(f"Received ClearChargingProfileRequest: id={charging_profile_id}, criteria={charging_profile_criteria}")
        self._clear_charging_profile_data = {
            'charging_profile_id': charging_profile_id,
            'charging_profile_criteria': charging_profile_criteria,
        }
        self._received_clear_charging_profile.set()
        return call_result.ClearChargingProfile(
            status=ClearChargingProfileStatusEnumType.accepted
        )


@pytest.mark.asyncio
async def test_tc_k_05():
    """Clear Charging Profile - With chargingProfileId."""
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

    # Memory State: Wait for CSMS to send GetChargingProfilesRequest
    async def trigger_get_profiles():
        await asyncio.sleep(1)
        await send_call(cp_id, "GetChargingProfiles", {
            "requestId": 1,
            "chargingProfile": {
                "chargingProfilePurpose": "TxDefaultProfile",
            },
            "evseId": EVSE_ID,
        })
    trigger_task1 = asyncio.create_task(trigger_get_profiles())

    await asyncio.wait_for(
        cp._received_get_charging_profiles.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task1.cancel()

    # Send ReportChargingProfilesRequest back to CSMS
    request_id = cp._get_charging_profiles_data['request_id']
    report_payload = call.ReportChargingProfiles(
        request_id=request_id,
        charging_limit_source=ChargingLimitSourceEnumType.cso,
        charging_profile=[{
            'id': cp._charging_profile_id,
            'stack_level': 1,
            'charging_profile_purpose': 'TxDefaultProfile',
            'charging_profile_kind': 'Absolute',
            'charging_schedule': [{
                'id': 1,
                'charging_rate_unit': 'A',
                'charging_schedule_period': [{'start_period': 0, 'limit': 6.0}],
            }],
        }],
        evse_id=EVSE_ID,
    )
    await cp.call(report_payload)

    # Main: Wait for CSMS to send ClearChargingProfileRequest
    async def trigger_clear_profile():
        await asyncio.sleep(1)
        await send_call(cp_id, "ClearChargingProfile", {
            "chargingProfileId": cp._charging_profile_id,
        })
    trigger_task2 = asyncio.create_task(trigger_clear_profile())

    await asyncio.wait_for(
        cp._received_clear_charging_profile.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task2.cancel()

    assert cp._clear_charging_profile_data is not None
    req_data = cp._clear_charging_profile_data

    # chargingProfileId must be present
    assert req_data['charging_profile_id'] is not None, \
        "chargingProfileId must be present"

    # chargingProfileCriteria should be omitted
    criteria = req_data['charging_profile_criteria']
    assert criteria is None, \
        f"Expected chargingProfileCriteria to be omitted, got {criteria}"

    logging.info("TC_K_05 completed successfully")
    start_task.cancel()
    await ws.close()
