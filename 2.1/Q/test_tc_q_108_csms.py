"""
Test case name      V2X Authorisation - ISO15118-20 - Central V2X control with charging schedule
Test case Id        TC_Q_108_CSMS
Use case Id(s)      Q03
Requirement(s)      Q03.FR.01, Q03.FR.02

Requirement Details:
    Q03.FR.01: CSMS SHALL send a SetChargingProfileRequest message with one or more chargingSchedulePeriod(s)
               that have operationMode = CentralSetpoint.
        Precondition: When CSMS provides setpoints for charging/discharging
    Q03.FR.02: CSMS SHALL provide a value for setpoint.
        Precondition: Q03.FR.01
        Note: This optionally includes the L2 and L3 variants of setpoint
System under test   CSMS

Description         To allow the CSMS to control the charge and discharge behaviour of an EV with power
                    profiles.

Purpose             To verify the CSMS is able to set a charging profile with a setpoint in the ISO15118-20
                    transaction.

Prerequisite(s)     CSMS supports ISO15118-20

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is ISO15118-20 transaction started in V2X AC_BPT energy transfer mode exposing:
                    - <allowedEnergyTransferModes>
                    - <transactionId>

Test Scenario
1. CSMS sends a SetChargingProfileRequest
2. Test System responds with a SetChargingProfileResponse with
    - status Accepted

Tool validations
* Step 1:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfile.transactionId must be <transactionId>
    - chargingProfile.chargingProfilePurpose must be TxProfile
    - chargingProfile.chargingSchedule.chargingRateUnit must be W
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].startPeriod must be 0
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].operationMode must be CentralSetpoint
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].setpoint must be 10.000
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].numberPhases may be present
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].phaseToUse may be present
    - all other fields in chargingProfile.chargingSchedule.chargingSchedulePeriod[0] must be absent

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.iso15118_20_transaction_just_started import V2X_VARIABLES
from reusable_states.iso15118_20_transaction_started_in_v2x_ac_bpt_energy_transfer_mode import (
    iso15118_20_transaction_started_in_v2x_ac_bpt_energy_transfer_mode,
)
from reusable_states.iso15118_smart_charging import validate_tx_profile
from smart_charging import only_schedule, request_charging_profile, tx_profile_id, v2x_profile
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])

# chargingSchedulePeriod[0].setpoint of the scenario: "10.000", in W
SETPOINT = 10000


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_q_108(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # The Test System supports ISO 15118-20 and V2X.
    cp.variables = dict(V2X_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is ISO15118-20 transaction started in V2X AC_BPT energy transfer mode
    #                 exposing <allowedEnergyTransferModes> and <transactionId>
    _, transaction_id = await iso15118_20_transaction_started_in_v2x_ac_bpt_energy_transfer_mode(cp)

    # 1. CSMS sends a SetChargingProfileRequest
    # 2. Test System responds with a SetChargingProfileResponse with
    #    - status Accepted
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, v2x_profile(
        'TxProfile', 'Absolute', {'operationMode': 'CentralSetpoint', 'setpoint': SETPOINT},
        profile_id=tx_profile_id(cp, transaction_id), transactionId=transaction_id))
    # evseId <Configured evseId>, chargingProfile.transactionId <transactionId>,
    # chargingProfilePurpose TxProfile
    validate_tx_profile(request, transaction_id)
    schedule = only_schedule(request)
    assert schedule.charging_rate_unit == 'W', \
        f"Expected chargingSchedule.chargingRateUnit W, got {schedule.charging_rate_unit}"
    period = schedule.charging_schedule_period[0]
    assert period.start_period == 0, \
        f"Expected chargingSchedulePeriod[0].startPeriod 0, got {period.start_period}"
    assert period.operation_mode == 'CentralSetpoint', \
        f"Expected chargingSchedulePeriod[0].operationMode CentralSetpoint, got {period.operation_mode}"
    assert period.setpoint == SETPOINT, \
        f"Expected chargingSchedulePeriod[0].setpoint {SETPOINT}, got {period.setpoint}"
    # numberPhases and phaseToUse may be present; all other fields in chargingSchedulePeriod[0]
    # must be absent
    others = set(period) - {'start_period', 'operation_mode', 'setpoint', 'number_phases',
                            'phase_to_use', 'custom_data'}
    assert not others, f"chargingSchedulePeriod[0] has fields that must be absent: {sorted(others)}"

    start_task.cancel()
