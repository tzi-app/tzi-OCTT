"""
Test case name      ISO 15118-20 Dynamic Control Mode - Adjusting charging schedule
Test case Id        TC_K_117_CSMS
Use case Id(s)      K20
Requirement(s)      K20.FR.03

Requirement Details:
    K20.FR.03: CSMS calculates a new charging profile and sends a SetChargingProfileRequest to Charging
               Station
        Precondition: K20.FR.01 AND EV and Charging Station use ISO 15118-20 "Dynamic Control Mode"
System under test   CSMS

Description         The EV signals the Charging Station that it wants to renegotiate and it provides new
                    charging needs, which the Charging Station sends to the CSMS. Based on this and other
                    parameters, the CSMS calculates a new charging schedule and sends it via
                    SetChargingProfileRequest to Charging Station, which communicates it to the EV.

Purpose             To verify if the CSMS is able to provide a new charging profile when EV provides a changed
                    departure time or target energy amount.

Prerequisite(s)     CSMS supports ISO15118-20

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized
                    State is EVConnectedPreSession
                    State is ISO15118SmartCharging (iso15118-20)

Test Scenario
1. The Test System sends a NotifyEVChargingNeedsRequest with
    - evseId <Configured evseId>
    - maxScheduleTuples 3
    - chargingNeeds.requestedEnergyTransfer AC_BPT
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
    - chargingNeeds.controlMode DynamicControl
    - chargingNeeds.departureTime <Current DateTime + 2 hours>
    - chargingNeeds.v2xChargingParameters.evTargetEnergyRequest 1000
    - chargingNeeds.v2xChargingParameters.maxChargePower 5000
    - chargingNeeds.v2xChargingParameters.maxDischargePower 5000
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
7. The Test System sends a NotifyEVChargingNeedsRequest with
    - evseId <Configured evseId>
    - maxScheduleTuples 3
    - chargingNeeds.requestedEnergyTransfer AC_BPT
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
    - chargingNeeds.controlMode DynamicControl
    - chargingNeeds.departureTime <Current DateTime + 3 hours>
    - chargingNeeds.v2xChargingParameters.evTargetEnergyRequest 1000
    - chargingNeeds.v2xChargingParameters.maxChargePower 5000
    - chargingNeeds.v2xChargingParameters.maxDischargePower 5000
8. The CSMS responds with a NotifyEVChargingNeedsResponse.
9. The CSMS sends a SetChargingProfileRequest
    Note(s):
    - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
      request
10. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
11. The Test System sends a NotifyEVChargingScheduleRequest with
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 5>
12. The CSMS responds with a NotifyEVChargingScheduleResponse.
13. The Test System sends a NotifyEVChargingNeedsRequest with
    - evseId <Configured evseId>
    - maxScheduleTuples 3
    - chargingNeeds.requestedEnergyTransfer AC_BPT
    - chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
    - chargingNeeds.controlMode DynamicControl
    - chargingNeeds.departureTime <Current DateTime + 3 hours>
    - chargingNeeds.v2xChargingParameters.evTargetEnergyRequest 3000
    - chargingNeeds.v2xChargingParameters.maxChargePower 5000
    - chargingNeeds.v2xChargingParameters.maxDischargePower 5000
14. The CSMS responds with a NotifyEVChargingNeedsResponse.
15. The CSMS sends a SetChargingProfileRequest
    Note(s):
    - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
      request
16. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
17. The Test System sends a NotifyEVChargingScheduleRequest with
    - evseId <Configured evseId>
    - chargingSchedule <ChargingSchedule provided at step 5>
18. The CSMS responds with a NotifyEVChargingScheduleResponse.

Tool validations
* Step 2:
    Message: NotifyEVChargingNeedsResponse
    - status must be Accepted or Processing
* Step 3:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfilePurpose must be TxProfile
    - transactionId must be <Provided transactionId from before>
    - chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpoint must be <Not omitted>
* Step 6:
    Message: NotifyEVChargingScheduleResponse
    - status must be Accepted
* Step 8:
    Message: NotifyEVChargingNeedsResponse
    - status must be Accepted or Processing
* Step 9:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfilePurpose must be TxProfile
    - transactionId must be <Provided transactionId from before>
* Step 12:
    Message: NotifyEVChargingScheduleResponse
    - status must be Accepted
* Step 14:
    Message: NotifyEVChargingNeedsResponse
    - status must be Accepted or Processing
* Step 15:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfilePurpose must be TxProfile
    - transactionId must be <Provided transactionId from before>
* Step 18:
    Message: NotifyEVChargingScheduleResponse
    - status must be Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
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


def charging_needs(departure_in_hours, ev_target_energy_request):
    """The chargingNeeds of the scenario, for a departure time and a target energy amount."""
    return {
        'requested_energy_transfer': 'AC_BPT',
        'available_energy_transfer': ['AC_single_phase', 'AC_three_phase', 'AC_BPT'],
        'control_mode': 'DynamicControl',
        'departure_time': utc_now_iso(departure_in_hours * 3600),
        'v2x_charging_parameters': {
            'ev_target_energy_request': ev_target_energy_request,
            'max_charge_power': 5000,
            'max_discharge_power': 5000,
        },
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_117(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # The Test System supports ISO 15118-20.
    cp.variables = dict(V2X_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State(s): State is Authorized, State is EVConnectedPreSession, State is
    #                    ISO15118SmartCharging (iso15118-20)
    await authorized(cp)
    await ev_connected_pre_session(cp)
    await iso15118_smart_charging(cp, 'iso15118-20')

    # 1. The Test System sends a NotifyEVChargingNeedsRequest with evseId <Configured evseId>,
    #    maxScheduleTuples 3, requestedEnergyTransfer AC_BPT, availableEnergyTransfer
    #    [AC_single_phase, AC_three_phase, AC_BPT], controlMode DynamicControl,
    #    - chargingNeeds.departureTime <Current DateTime + 2 hours>
    #    - chargingNeeds.v2xChargingParameters.evTargetEnergyRequest 1000
    #    - chargingNeeds.v2xChargingParameters.maxChargePower 5000
    #    - chargingNeeds.v2xChargingParameters.maxDischargePower 5000
    # 2. The CSMS responds with a NotifyEVChargingNeedsResponse.
    #    - status must be Accepted or Processing
    # 3. The CSMS sends a SetChargingProfileRequest
    #    Note(s): If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will
    #    wait 60 seconds for the request
    #    - evseId must be <Configured evseId>, chargingProfilePurpose must be TxProfile,
    #      transactionId must be <Provided transactionId from before>
    # 4. The Test System responds with a SetChargingProfileResponse with status Accepted
    request = await negotiate_charging_schedule(
        cp, charging_needs(departure_in_hours=2, ev_target_energy_request=1000), max_schedule_tuples=3)
    # chargingProfile.chargingSchedule[0].chargingSchedulePeriod[0].setpoint must be <Not omitted>
    first_period = request.charging_profile.charging_schedule[0].charging_schedule_period[0]
    assert first_period.setpoint is not None, \
        f"chargingSchedule[0].chargingSchedulePeriod[0].setpoint must not be omitted: {first_period}"

    # 5. The Test System sends a NotifyEVChargingScheduleRequest with evseId <Configured evseId>
    #    and chargingSchedule <ChargingSchedule provided at step 3>
    # 6. The CSMS responds with a NotifyEVChargingScheduleResponse.
    #    - status must be Accepted
    await notify_ev_charging_schedule(
        cp, request.charging_profile.charging_schedule[0], selected=True)

    # 7. The Test System sends a NotifyEVChargingNeedsRequest as in step 1, with
    #    - chargingNeeds.departureTime <Current DateTime + 3 hours>
    #    - chargingNeeds.v2xChargingParameters.evTargetEnergyRequest 1000
    # 8. The CSMS responds with a NotifyEVChargingNeedsResponse.
    #    - status must be Accepted or Processing
    # 9. The CSMS sends a SetChargingProfileRequest (as in step 3)
    # 10. The Test System responds with a SetChargingProfileResponse with status Accepted
    request = await negotiate_charging_schedule(
        cp, charging_needs(departure_in_hours=3, ev_target_energy_request=1000), max_schedule_tuples=3)

    # 11. The Test System sends a NotifyEVChargingScheduleRequest with evseId <Configured
    #     evseId> and the chargingSchedule that the CSMS provided, at step 9
    # 12. The CSMS responds with a NotifyEVChargingScheduleResponse.
    #     - status must be Accepted
    await notify_ev_charging_schedule(
        cp, request.charging_profile.charging_schedule[0], selected=True)

    # 13. The Test System sends a NotifyEVChargingNeedsRequest as in step 1, with
    #     - chargingNeeds.departureTime <Current DateTime + 3 hours>
    #     - chargingNeeds.v2xChargingParameters.evTargetEnergyRequest 3000
    # 14. The CSMS responds with a NotifyEVChargingNeedsResponse.
    #     - status must be Accepted or Processing
    # 15. The CSMS sends a SetChargingProfileRequest (as in step 3)
    # 16. The Test System responds with a SetChargingProfileResponse with status Accepted
    request = await negotiate_charging_schedule(
        cp, charging_needs(departure_in_hours=3, ev_target_energy_request=3000), max_schedule_tuples=3)

    # 17. The Test System sends a NotifyEVChargingScheduleRequest with evseId <Configured
    #     evseId> and the chargingSchedule that the CSMS provided, at step 15
    # 18. The CSMS responds with a NotifyEVChargingScheduleResponse.
    #     - status must be Accepted
    await notify_ev_charging_schedule(
        cp, request.charging_profile.charging_schedule[0], selected=True)

    start_task.cancel()
