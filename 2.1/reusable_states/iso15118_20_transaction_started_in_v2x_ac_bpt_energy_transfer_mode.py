"""
State               ISO15118-20 transaction started in V2X AC_BPT energy transfer mode
System under test   CSMS
Description         Starts ISO15118-20 transaction and upgrades to V2X AC_BPT energy transfer mode
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      State is ISO15118-20 transaction just started exposing:
                            - <allowedEnergyTransferModes>
                            - <transactionId>

Main

Agree on energy transfer mode

1. The Test System sends a NotifyEVChargingNeedsRequest with:
   evseId = <Configured evseId>
   chargingNeeds.requestedEnergyTransfer = AC_BPT
   chargingNeeds.availableEnergyTransfer = [AC_single_phase, AC_two_phase, AC_three_phase, AC_BPT, AC_BPT_DER,
   AC_DER]
   chargingNeeds.controlMode = ScheduledControl
   chargingNeeds.v2xChargingParameters.maxChargePower = 1234W
   chargingNeeds.v2xChargingParameters.maxDischargePower = 0W
2. The CSMS responds with a NotifyEVChargingNeedsResponse

Tool validations
* Step 2: Message: NotifyEVChargingNeedsResponse - status must be Accepted or Processing
Post condition      N/a

Remarks
Exposes <allowedEnergyTransferModes>
<transactionId>
"""

import asyncio
import os

from ocpp.v21 import call

from charge_point import NO_ACTION_WAIT, ChargingSession, TziChargePoint21
from reusable_states.iso15118_20_transaction_just_started import iso15118_20_transaction_just_started

CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


async def iso15118_20_transaction_started_in_v2x_ac_bpt_energy_transfer_mode(
        cp: TziChargePoint21, evse_id: int = CONFIGURED_EVSE_ID, session: ChargingSession = None):
    """Returns what the state exposes: (<allowedEnergyTransferModes>, <transactionId>).

    session: the charging session this is about, when the scenario has more than one."""
    session = session or cp.session

    # Before: State is ISO15118-20 transaction just started exposing
    #         <allowedEnergyTransferModes> and <transactionId>
    allowed_energy_transfer_modes, transaction_id = \
        await iso15118_20_transaction_just_started(cp, session=session)

    # Agree on energy transfer mode
    # 1. The Test System sends a NotifyEVChargingNeedsRequest with:
    #    evseId = <Configured evseId>
    #    chargingNeeds.requestedEnergyTransfer = AC_BPT
    #    chargingNeeds.availableEnergyTransfer = [AC_single_phase, AC_two_phase,
    #    AC_three_phase, AC_BPT, AC_BPT_DER, AC_DER]
    #    chargingNeeds.controlMode = ScheduledControl
    #    chargingNeeds.v2xChargingParameters.maxChargePower = 1234W
    #    chargingNeeds.v2xChargingParameters.maxDischargePower = 0W
    # 2. The CSMS responds with a NotifyEVChargingNeedsResponse
    cp.forget_requests('SetChargingProfile')
    cp.set_response('SetChargingProfile', status='Accepted')
    response = await cp.call(call.NotifyEVChargingNeeds(
        evse_id=evse_id,
        charging_needs={
            'requested_energy_transfer': 'AC_BPT',
            'available_energy_transfer': ['AC_single_phase', 'AC_two_phase', 'AC_three_phase',
                                          'AC_BPT', 'AC_BPT_DER', 'AC_DER'],
            'control_mode': 'ScheduledControl',
            'v2x_charging_parameters': {'max_charge_power': 1234, 'max_discharge_power': 0},
        },
    ))
    assert response.status in ('Accepted', 'Processing'), \
        f"Expected NotifyEVChargingNeedsResponse.status Accepted or Processing, got {response.status}"

    # With these statuses the CSMS provides a charging profile, immediately or soon
    # (Q01.FR.07). The state does not validate it; the Test System gives it a moment to
    # arrive, so that the scenario that follows does not take it for one of its own steps.
    try:
        await cp.wait_for_request('SetChargingProfile', timeout=NO_ACTION_WAIT)
    except asyncio.TimeoutError:
        pass

    return allowed_energy_transfer_modes, transaction_id
