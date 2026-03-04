"""
TC_K_29 - Get Charging Profile - EvseId 0
Use case: K09 | Requirements: K09.FR.03
K09.FR.03: The CSMS SHALL specify in chargingProfile criteria in GetChargingProfilesRequest either: - a (list of) chargingProfileId(s) OR - one or more of the fields stackLevel, chargingLimitSource, chargingProfilePurpose. These fields are filter values of equal importance, but because a chargingProfileId uniquely identifies a
System under test: CSMS

Description:
    With the GetChargingProfilesRequest message the CSMS can ask a Charging Station to report all, or a
    subset of all the install Charging Profiles from the different possible sources.

Purpose:
    To verify if the CSMS is able to request charging profiles installed on the charging station itself and
    read in the reports as described at the OCPP specification.

Before:
    Charging State: EnergyTransferStarted

Main:
    1. The CSMS sends a GetChargingProfilesRequest with evseId 0
    2. The OCTT responds with a GetChargingProfilesResponse with status Accepted
    3. The OCTT sends a ReportChargingProfilesRequest with requestId <Received requestId>
    4. The CSMS responds with a ReportChargingProfilesResponse

Tool validations:
    * Step 1: Message GetChargingProfilesRequest
      - evseId 0 AND
      - chargingProfile.chargingProfilePurpose <Configured chargingProfilePurpose>
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
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started
from trigger import send_call

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
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


@pytest.mark.asyncio
async def test_tc_k_29():
    """Get Charging Profile - EvseId 0."""
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

    transaction_id = generate_transaction_id()

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Before: Execute Reusable State EnergyTransferStarted
    await authorized(cp, id_token_id=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE,
                     transaction_id=transaction_id, evse_id=EVSE_ID, connector_id=CONNECTOR_ID)
    await energy_transfer_started(cp, evse_id=EVSE_ID, connector_id=CONNECTOR_ID,
                                  transaction_id=transaction_id)

    # Step 1-2: Wait for CSMS to send GetChargingProfilesRequest
    async def trigger_get_profiles():
        await asyncio.sleep(1)
        await send_call(cp_id, "GetChargingProfiles", {"requestId": 1, "chargingProfile": {"chargingProfilePurpose": "TxDefaultProfile"}, "evseId": 0})
    trigger_task = asyncio.create_task(trigger_get_profiles())

    await asyncio.wait_for(
        cp._received_get_charging_profiles.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    trigger_task.cancel()

    assert cp._get_charging_profiles_data is not None
    req_data = cp._get_charging_profiles_data

    # evseId must be 0
    assert req_data['evse_id'] == 0, \
        f"Expected evseId=0, got {req_data['evse_id']}"

    # Tool validations for chargingProfile criterion
    criterion = req_data['charging_profile']
    purpose = criterion.get('charging_profile_purpose')
    if purpose is None:
        purpose = criterion.get('chargingProfilePurpose')
    stack_level = criterion.get('stack_level')
    if stack_level is None:
        stack_level = criterion.get('stackLevel')
    limit_source = criterion.get('charging_limit_source')
    if limit_source is None:
        limit_source = criterion.get('chargingLimitSource')
    profile_id = criterion.get('charging_profile_id')
    if profile_id is None:
        profile_id = criterion.get('chargingProfileId')

    assert purpose is not None, "chargingProfilePurpose must be present in criterion"
    assert stack_level is None, f"Expected stackLevel to be omitted, got {stack_level}"
    assert limit_source is None, f"Expected chargingLimitSource to be omitted, got {limit_source}"
    assert profile_id is None, f"Expected chargingProfileId to be omitted, got {profile_id}"

    # Step 3: Send ReportChargingProfilesRequest
    request_id = req_data['request_id']
    report_payload = call.ReportChargingProfiles(
        request_id=request_id,
        charging_limit_source=ChargingLimitSourceEnumType.cso,
        charging_profile=[{
            'id': 1,
            'stack_level': 1,
            'charging_profile_purpose': 'TxDefaultProfile',
            'charging_profile_kind': 'Absolute',
            'charging_schedule': [{
                'id': 1,
                'charging_rate_unit': 'A',
                'charging_schedule_period': [{'start_period': 0, 'limit': 6.0}],
            }],
        }],
        evse_id=0,
    )
    # Step 4: CSMS responds with ReportChargingProfilesResponse
    await cp.call(report_payload)

    logging.info("TC_K_29 completed successfully")
    start_task.cancel()
    await ws.close()
