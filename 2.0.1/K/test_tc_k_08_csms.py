"""
TC_K_08 - Clear Charging Profile - Without previous charging profile
Use case: K10 | Requirements: N/a
System under test: CSMS

Description:
    If the CSMS wishes to clear some or all of the charging profiles that were previously sent to the
    Charging Station, then the CSMS sends a ClearChargingProfileRequest to the Charging Station.

Purpose:
    To verify if the CSMS is able to request the charging station to clear a specific charging profile with a
    chargingProfileId and stackLevel/purpose combination while the Charging stations does not accept as
    described at the OCPP specification.

Main:
    1. The CSMS sends a ClearChargingProfileRequest with
       chargingProfilePurpose TxDefaultProfile AND evseId <Configured evseId> AND
       stackLevel <Configured stackLevel>
    2. The OCTT responds with a ClearChargingProfileResponse with status Unknown

Tool validations:
    * Step 1: Message ClearChargingProfileRequest
      - chargingProfilePurpose TxDefaultProfile AND
      - evseId <Configured evseId> AND
      - stackLevel <Configured stackLevel>
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
    ClearChargingProfileStatusEnumType,
    ChargingProfilePurposeEnumType,
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
        self._received_clear_charging_profile = asyncio.Event()
        self._clear_charging_profile_data = None

    @on(Action.clear_charging_profile)
    async def on_clear_charging_profile(self, charging_profile_id=None, charging_profile_criteria=None, **kwargs):
        logging.info(f"Received ClearChargingProfileRequest: id={charging_profile_id}, criteria={charging_profile_criteria}")
        self._clear_charging_profile_data = {
            'charging_profile_id': charging_profile_id,
            'charging_profile_criteria': charging_profile_criteria,
        }
        self._received_clear_charging_profile.set()
        return call_result.ClearChargingProfile(
            status=ClearChargingProfileStatusEnumType.unknown
        )


@pytest.mark.asyncio
async def test_tc_k_08():
    """Clear Charging Profile - Without previous charging profile."""
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

    await asyncio.wait_for(
        cp._received_clear_charging_profile.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._clear_charging_profile_data is not None
    req_data = cp._clear_charging_profile_data
    criteria = req_data['charging_profile_criteria']

    assert criteria is not None, "chargingProfileCriteria must be present"

    # chargingProfileId must be omitted
    assert req_data['charging_profile_id'] is None, \
        f"Expected chargingProfileId to be omitted, got {req_data['charging_profile_id']}"

    # chargingProfilePurpose must be TxDefaultProfile
    purpose = criteria.get('charging_profile_purpose') or criteria.get('chargingProfilePurpose')
    assert purpose in ('TxDefaultProfile', ChargingProfilePurposeEnumType.tx_default_profile), \
        f"Expected purpose=TxDefaultProfile, got {purpose}"

    # stackLevel must be present
    stack_level = criteria.get('stack_level') or criteria.get('stackLevel')
    assert stack_level is not None, "stackLevel must be present"

    # evseId must be configured evseId
    evse_id = criteria.get('evse_id') if criteria.get('evse_id') is not None else criteria.get('evseId')
    assert evse_id == EVSE_ID, \
        f"Expected evseId={EVSE_ID}, got {evse_id}"

    # Step 2: Response is Unknown (handled by handler above)

    logging.info("TC_K_08 completed successfully")
    start_task.cancel()
    await ws.close()
