"""
TC_K_60 - Set Charging Profile - TxProfile with ongoing transaction on the specified EVSE
Use case: K01 | Requirements: K01.FR.03, K01.FR.31
K01.FR.03: The CSMS SHALL include the transactionId in the SetChargingProfileRequest when setting a TxProfile. The transactionId is used to match the profile to a specific transaction.
K01.FR.31: The startPeriod of the first chargingSchedulePeriod in a chargingSchedule SHALL always be 0.
System under test: CSMS

Description:
    The CSMS sets a TxProfile on a specific EVSE for a currently ongoing transaction.

Purpose:
    To verify if the CSMS is able to exchange messages to set a TxProfile on a specific EVSE for a currently
    ongoing transaction.

Before:
    Reusable State: EnergyTransferStarted

Main:
    1. The CSMS sends a SetChargingProfileRequest
    2. The OCTT responds with a SetChargingProfileResponse with status Accepted

Tool validations:
    * Step 1: (Message: SetChargingProfileRequest)
      - chargingProfile.chargingProfilePurpose is TxProfile AND
      - chargingProfile.evseId is <Configured evseId> AND
      - chargingProfile.transactionId <Generated transactionId> AND
      - chargingProfile.chargingProfileKind is Relative OR Absolute
      If chargingProfileKind is Relative then chargingSchedule.startSchedule must be omitted.
      If chargingProfileKind is Absolute then chargingSchedule.startSchedule must NOT be omitted.
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
from utils import get_basic_auth_headers, generate_transaction_id, now_iso, build_default_ssl_context
from reusable_states.authorized import authorized
from reusable_states.energy_transfer_started import energy_transfer_started

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
async def test_tc_k_60():
    """Set Charging Profile - TxProfile with ongoing transaction."""
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

    # Step 1-2: Wait for CSMS to send SetChargingProfileRequest
    await asyncio.wait_for(
        cp._received_set_charging_profile.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._set_charging_profile_data is not None
    req_data = cp._set_charging_profile_data
    profile = req_data['charging_profile']

    # chargingProfilePurpose must be TxProfile
    purpose = profile.get('charging_profile_purpose') or profile.get('chargingProfilePurpose')
    assert purpose in ('TxProfile', ChargingProfilePurposeEnumType.tx_profile), \
        f"Expected purpose=TxProfile, got {purpose}"

    # evseId must be configured evseId
    assert req_data['evse_id'] == EVSE_ID, \
        f"Expected evseId={EVSE_ID}, got {req_data['evse_id']}"

    # transactionId must be the generated transactionId
    tx_id = profile.get('transaction_id') or profile.get('transactionId')
    assert tx_id == transaction_id, \
        f"Expected transactionId={transaction_id}, got {tx_id}"

    # chargingProfileKind must be Relative or Absolute
    kind = profile.get('charging_profile_kind') or profile.get('chargingProfileKind')
    assert kind in ('Relative', 'Absolute', ChargingProfileKindEnumType.relative, ChargingProfileKindEnumType.absolute), \
        f"Expected kind=Relative or Absolute, got {kind}"

    # Conditional startSchedule validation based on chargingProfileKind
    schedules = profile.get('charging_schedule') or profile.get('chargingSchedule')
    assert schedules is not None and len(schedules) > 0, "chargingSchedule must be present"
    schedule = schedules[0] if isinstance(schedules, list) else schedules

    start_schedule = schedule.get('start_schedule') or schedule.get('startSchedule')
    if kind in ('Relative', ChargingProfileKindEnumType.relative):
        assert start_schedule is None, \
            f"Expected startSchedule to be omitted for Relative kind, got {start_schedule}"
    elif kind in ('Absolute', ChargingProfileKindEnumType.absolute):
        assert start_schedule is not None, \
            "Expected startSchedule to be present for Absolute kind"

    # K01.FR.31: The startPeriod of the first chargingSchedulePeriod SHALL always be 0
    periods = schedule.get('charging_schedule_period') or schedule.get('chargingSchedulePeriod')
    assert periods is not None and len(periods) > 0, "chargingSchedulePeriod must be present"
    first_period = periods[0]
    start_period = first_period.get('start_period') if first_period.get('start_period') is not None else first_period.get('startPeriod')
    assert start_period == 0, f"K01.FR.31: Expected startPeriod=0, got {start_period}"

    logging.info("TC_K_60 completed successfully")
    start_task.cancel()
    await ws.close()
