"""
Test case name      Renegotiating a Charging Schedule ISO 15118-20 - Initiated by EV
Test case Id        TC_K_114_CSMS
Use case Id(s)      K17
Requirement(s)      K17.FR.02, K17.FR.03, K17.FR.05, K17.FR.07, K17.FR.08, K17.FR.11

Requirement Details:
    K17.FR.02: In response to a NotifyEVChargingNeedsRequest the CSMS SHALL send a
               NotifyEVChargingNeedsResponse.
        Precondition: K17.FR.01
    K17.FR.03: CSMS SHALL indicate this by setting the status field in the NotifyEVChargingNeedsResponse to
               'Accepted'.
        Precondition: K17.FR.02 AND If the CSMS is able to provide a charging schedule now
    K17.FR.05: CSMS SHALL indicate this by setting the status field in the NotifyEVChargingNeedsResponse to
               'Processing'.
        Precondition: K17.FR.02 AND If the CSMS is able to provide a charging schedule, but needs processing
                      time
    K17.FR.07 (2.1): The CSMS SHALL send a SetChargingProfileRequest with chargingProfilePurpose = TxProfile
                     and at most three chargingSchedule and optional price schedule elements, that each
                     contain no more periods than specified by maxScheduleTuples in
                     NotifyEVChargingNeedsRequest and by device model variable
                     SmartChargingCtrlr.PeriodsPerSchedule.
        Precondition: (K17.FR.03 OR K17.FR.05) AND controlMode is ScheduledControl or absent
    K17.FR.08: The CSMS SHOULD send a SetChargingProfileRequest to the Charging Station within 60 seconds.
        Precondition: K17.FR.01
        Note: This is to satisfy the ISO 15118 ChargeParameterDiscoveryReq timeout.
    K17.FR.11 (2.1): CSMS responds with NotifyEVChargingScheduleResponse with status Accepted to Charging
                     Station.
        Precondition: K17.FR.10 AND EV charging profile is within limits of CSMS ChargingSchedule
        Note: Note: Already checked by Charging Station, but CSMS does its own check. Not applicable in
              dynamic control mode.
System under test   CSMS

Description         The EV signals the Charging Station that it wants to renegotiate and it provides new
                    charging needs, which the Charging Station sends to the CSMS. Based on this and other
                    parameters, the CSMS calculates a new charging schedule and sends it via
                    SetChargingProfileRequest to Charging Station, which communicates it to the EV.

Purpose             To verify if the CSMS is able to renegotiate when the EV signals the Charging Station that
                    it wants to renegotiate and it provides new charging needs, which the Charging Station
                    sends to the CSMS.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession
                    State is Authorized
                    State is ISO15118SmartCharging (iso15118-20)

Test Scenario
1. The Test System sends a NotifyEVChargingNeedsRequest with
    - evseId <Configured evseId>
    - maxScheduleTuples 1
    - chargingNeeds.requestedEnergyTransfer AC_three_phase
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
    - chargingNeeds.controlMode ScheduledControl
    - chargingNeeds.v2xChargingParameters.maxChargePower 6000
    - chargingNeeds.v2xChargingParameters.maxDischargePower 0
2. The CSMS responds with a NotifyEVChargingNeedsResponse.
3. The CSMS sends a SetChargingProfileRequest
    Note(s):
    - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
      request
4. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
5. The Test System sends a NotifyEVChargingScheduleRequest with
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 3>
6. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 2:
    Message: NotifyEVChargingNeedsResponse
    - status must be Accepted or Processing
* Step 3:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfilePurpose must be TxProfile
    - transactionId must be <Provided transactionId from before>
    - chargingProfile.chargingSchedule must be size = 1
* Step 6:
    Message: NotifyEVChargingScheduleResponse
    - status must be Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.authorized import authorized
from reusable_states.booted import booted
from reusable_states.ev_connected_pre_session import ev_connected_pre_session
from reusable_states.iso15118_20_transaction_just_started import V2X_VARIABLES
from reusable_states.iso15118_smart_charging import (
    iso15118_smart_charging,
    negotiate_charging_schedule,
    notify_ev_charging_schedule,
)
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_114(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # The Test System supports ISO 15118-20.
    cp.variables = dict(V2X_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State(s): State is EVConnectedPreSession, State is Authorized, State is
    #                    ISO15118SmartCharging (iso15118-20)
    await ev_connected_pre_session(cp)
    await authorized(cp)
    await iso15118_smart_charging(cp, 'iso15118-20')

    # 1. The Test System sends a NotifyEVChargingNeedsRequest with
    #    - evseId <Configured evseId>
    #    - maxScheduleTuples 1
    #    - chargingNeeds.requestedEnergyTransfer AC_three_phase
    #    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
    #    - chargingNeeds.controlMode ScheduledControl
    #    - chargingNeeds.v2xChargingParameters.maxChargePower 6000
    #    - chargingNeeds.v2xChargingParameters.maxDischargePower 0
    # 2. The CSMS responds with a NotifyEVChargingNeedsResponse.
    #    - status must be Accepted or Processing
    # 3. The CSMS sends a SetChargingProfileRequest
    #    Note(s): If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will
    #    wait 60 seconds for the request
    #    - evseId must be <Configured evseId>, chargingProfilePurpose must be TxProfile,
    #      transactionId must be <Provided transactionId from before>
    # 4. The Test System responds with a SetChargingProfileResponse with
    #    - status Accepted
    request = await negotiate_charging_schedule(cp, {
        'requested_energy_transfer': 'AC_three_phase',
        'available_energy_transfer': ['AC_single_phase', 'AC_three_phase', 'AC_BPT'],
        'control_mode': 'ScheduledControl',
        'v2x_charging_parameters': {'max_charge_power': 6000, 'max_discharge_power': 0},
    }, max_schedule_tuples=1)
    # chargingProfile.chargingSchedule must be size = 1
    schedules = request.charging_profile.charging_schedule
    assert len(schedules) == 1, f"chargingProfile.chargingSchedule must be size = 1, got {len(schedules)}"

    # 5. The Test System sends a NotifyEVChargingScheduleRequest with
    #    - evseId <Configured evseId>
    #    - chargingSchedule <ChargingSchedule provided at step 3>
    # 6. The CSMS responds with a NotifyEVChargingScheduleResponse.
    #    - status must be Accepted
    await notify_ev_charging_schedule(cp, schedules[0], selected=True)

    start_task.cancel()
