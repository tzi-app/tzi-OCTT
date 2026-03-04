"""
TC_K_32 - Get Charging Profile - chargingProfileId
Use case: K09 | Requirements: K09.FR.03
K09.FR.03: The CSMS SHALL specify in chargingProfile criteria in GetChargingProfilesRequest either: - a (list of) chargingProfileId(s) OR - one or more of the fields stackLevel, chargingLimitSource, chargingProfilePurpose. These fields are filter values of equal importance, but because a chargingProfileId uniquely identifies a
System under test: CSMS

Purpose:
    To verify if the CSMS is able to request a specific charging profile and read in the reports as described
    at the OCPP specification.

Tool validations:
    * Step 1: Message GetChargingProfilesRequest
      - chargingProfileId <received chargingProfileId> AND
      - requestId <Generated Id>
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
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


class SmartChargingMockCP(TziChargePoint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._received_get_charging_profiles = asyncio.Event()
        self._get_charging_profiles_data = None

    @on(Action.get_charging_profiles)
    async def on_get_charging_profiles(self, request_id, charging_profile, evse_id=None, **kwargs):
        logging.info(f"Received GetChargingProfilesRequest: request_id={request_id}, evse_id={evse_id}, profile={charging_profile}")
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
async def test_tc_k_32():
    """Get Charging Profile - chargingProfileId."""
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

    await asyncio.wait_for(cp._received_get_charging_profiles.wait(), timeout=CSMS_ACTION_TIMEOUT)

    req_data = cp._get_charging_profiles_data
    criterion = req_data['charging_profile']

    # evseId must be omitted
    assert req_data['evse_id'] is None, \
        f"Expected evseId to be omitted, got {req_data['evse_id']}"

    # chargingProfileId must be present in the criterion
    profile_ids = criterion.get('charging_profile_id')
    if profile_ids is None:
        profile_ids = criterion.get('chargingProfileId')
    assert profile_ids is not None, "chargingProfileId must be present in criterion"

    # All other fields must be omitted
    purpose = criterion.get('charging_profile_purpose')
    if purpose is None:
        purpose = criterion.get('chargingProfilePurpose')
    stack_level = criterion.get('stack_level')
    if stack_level is None:
        stack_level = criterion.get('stackLevel')
    limit_source = criterion.get('charging_limit_source')
    if limit_source is None:
        limit_source = criterion.get('chargingLimitSource')
    assert purpose is None, f"Expected chargingProfilePurpose to be omitted, got {purpose}"
    assert stack_level is None, f"Expected stackLevel to be omitted, got {stack_level}"
    assert limit_source is None, f"Expected chargingLimitSource to be omitted, got {limit_source}"

    # requestId must be present
    assert req_data['request_id'] is not None, "requestId must be present"

    # Send ReportChargingProfilesRequest
    report_payload = call.ReportChargingProfiles(
        request_id=req_data['request_id'],
        charging_limit_source=ChargingLimitSourceEnumType.cso,
        charging_profile=[{
            'id': 1, 'stack_level': 1,
            'charging_profile_purpose': 'TxDefaultProfile',
            'charging_profile_kind': 'Absolute',
            'charging_schedule': [{'id': 1, 'charging_rate_unit': 'A',
                                   'charging_schedule_period': [{'start_period': 0, 'limit': 6.0}]}],
        }],
        evse_id=1,
    )
    await cp.call(report_payload)

    logging.info("TC_K_32 completed successfully")
    start_task.cancel()
    await ws.close()
