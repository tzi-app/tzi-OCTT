"""
State               ISO15118SmartCharging
System under test   CSMS
Description         A version for the ISO15118 can be specified as argument to this reusable state. This
                    version is exposed as variable <iso15118Version> and can either be iso15118-2 or
                    iso15118-20. If not specified iso15118-2 will be assumed.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

1. The Test System sends a NotifyEVChargingNeedsRequest with
   evseId <Configured evseId>
   maxScheduleTuples 2
   if <iso15118Version> is iso15118-2:
       chargingNeeds.requestedEnergyTransfer AC_three_phase
       chargingNeeds.acChargingParameters.energyAmount 50000
       chargingNeeds.acChargingParameters.evMinCurrent 0
       chargingNeeds.acChargingParameters.evMaxCurrent 32
       chargingNeeds.acChargingParameters.evMaxVoltage 230
   end if
   if <iso15118Version> is iso15118-20:
       chargingNeeds.requestedEnergyTransfer AC_single_phase
       chargingNeeds.availableEnergyTransfer [AC_single_phase, AC_three_phase, AC_BPT]
       chargingNeeds.controlMode ScheduledControl
       chargingNeeds.v2xChargingParameters.maxChargePower 10000
       chargingNeeds.v2xChargingParameters.maxDischargePower 10000
   end if
2. The CSMS responds with a NotifyEVChargingNeedsResponse.
3. The CSMS sends a SetChargingProfileRequest
   Note(s):
   - If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds for the
     request
4. The Test System responds with a SetChargingProfileResponse with:
   status Accepted
5. The Test System sends a NotifyEVChargingScheduleRequest with
   evseId <COnfigured evseId>
   chargingSchedule <ChargingSchedule provided at step 3>
6. The CSMS responds with a NotifyEVChargingScheduleResponse.
7. The Test System sends a TransactionEventRequest with
   triggerReason <ChargingStateChanged>
   transactionInfo.chargingState <Charging>
8. The CSMS responds with a TransactionEventResponse.

Tool validations
* Step 2: Message: NotifyEVChargingNeedsResponse - Status must be Accepted or Processing
* Step 3: Message: SetChargingProfileRequest
  - chargingProfilePurpose must be <TxProfile>
  - transactionId must be <Provided transactionId from before>
* Step 4: Message: NotifyEVChargingScheduleResponse - status must be <Accepted>
Post condition      N/a
"""

import os

from ocpp.v21 import call

from charge_point import ACTION_TIMEOUT, ChargingSession, TziChargePoint21
from ocpp_messages import utc_now_iso

CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])

# "If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will wait 60 seconds
# for the request"
PROCESSING_TIMEOUT = 60


def charging_needs(iso15118_version='iso15118-2'):
    """The chargingNeeds of the mock EV in this state, for ISO 15118-2 or ISO 15118-20."""
    if iso15118_version == 'iso15118-20':
        return {
            'requested_energy_transfer': 'AC_single_phase',
            'available_energy_transfer': ['AC_single_phase', 'AC_three_phase', 'AC_BPT'],
            'control_mode': 'ScheduledControl',
            'v2x_charging_parameters': {'max_charge_power': 10000, 'max_discharge_power': 10000},
        }
    return {
        'requested_energy_transfer': 'AC_three_phase',
        'ac_charging_parameters': {
            'energy_amount': 50000,
            'ev_min_current': 0,
            'ev_max_current': 32,
            'ev_max_voltage': 230,
        },
    }


async def negotiate_charging_schedule(cp: TziChargePoint21, needs: dict, max_schedule_tuples: int = 2,
                                      evse_id: int = CONFIGURED_EVSE_ID,
                                      session: ChargingSession = None,
                                      statuses=('Accepted', 'Processing'), validate: bool = True):
    """The Charging Station reports the charging needs of the EV, and the CSMS provides a
    charging profile for them:

        The Test System sends a NotifyEVChargingNeedsRequest
        The CSMS responds with a NotifyEVChargingNeedsResponse    - status one of `statuses`
        The CSMS sends a SetChargingProfileRequest                - evseId <Configured evseId>,
                                                                    chargingProfilePurpose
                                                                    TxProfile, transactionId
                                                                    of the transaction
        The Test System responds with a SetChargingProfileResponse with status Accepted

    validate=False leaves the validation of the SetChargingProfileRequest to the test case,
    when that has other validations for it. Returns the SetChargingProfileRequest.
    """
    session = session or cp.session
    # Only a SetChargingProfileRequest that follows these charging needs is the answer to them.
    cp.forget_requests('SetChargingProfile')
    cp.set_response('SetChargingProfile', status='Accepted')
    response = await cp.call(call.NotifyEVChargingNeeds(
        evse_id=evse_id, max_schedule_tuples=max_schedule_tuples, charging_needs=needs))
    assert response.status in statuses, \
        f"Expected NotifyEVChargingNeedsResponse.status {' or '.join(statuses)}, got {response.status}"

    request = await cp.wait_for_request(
        'SetChargingProfile',
        timeout=PROCESSING_TIMEOUT if response.status == 'Processing' else ACTION_TIMEOUT)
    if validate:
        validate_tx_profile(request, session.transaction_id, evse_id)
    return request


def validate_tx_profile(request, transaction_id, evse_id=CONFIGURED_EVSE_ID):
    """A SetChargingProfileRequest of the ISO 15118 test cases: evseId <Configured evseId>,
    chargingProfilePurpose TxProfile, transactionId <Provided transactionId from before>."""
    profile = request.charging_profile
    assert request.evse_id == evse_id, \
        f"Expected SetChargingProfileRequest.evseId {evse_id}, got {request.evse_id}"
    assert profile.charging_profile_purpose == 'TxProfile', \
        f"Expected chargingProfilePurpose TxProfile, got {profile.charging_profile_purpose}"
    assert profile.transaction_id == transaction_id, \
        f"Expected chargingProfile.transactionId {transaction_id}, got {profile.transaction_id}"


async def notify_ev_charging_schedule(cp: TziChargePoint21, schedule,
                                      evse_id: int = CONFIGURED_EVSE_ID, status: str = 'Accepted',
                                      selected: bool = False):
    """The Test System sends a NotifyEVChargingScheduleRequest with a charging schedule, and
    the CSMS responds with a NotifyEVChargingScheduleResponse with the given status.

    selected: the schedule is the one of the CSMS that the EV selected, and the request says
    so in selectedChargingScheduleId, as an ISO 15118-20 station does (K18.FR.10).
    """
    response = await cp.call(call.NotifyEVChargingSchedule(
        time_base=utc_now_iso(),
        evse_id=evse_id,
        charging_schedule=schedule,
        selected_charging_schedule_id=schedule['id'] if selected else None,
    ))
    assert response.status == status, \
        f"Expected NotifyEVChargingScheduleResponse.status {status}, got {response.status}"
    return response


async def iso15118_smart_charging(cp: TziChargePoint21, iso15118_version: str = 'iso15118-2',
                                  evse_id: int = CONFIGURED_EVSE_ID,
                                  session: ChargingSession = None):
    """Returns the SetChargingProfileRequest of the CSMS.

    session: the charging session this is about, when the scenario has more than one."""
    session = session or cp.session
    assert iso15118_version in ('iso15118-2', 'iso15118-20'), iso15118_version

    # 1. The Test System sends a NotifyEVChargingNeedsRequest with evseId <Configured evseId>,
    #    maxScheduleTuples 2 and the chargingNeeds of the <iso15118Version>
    # 2. The CSMS responds with a NotifyEVChargingNeedsResponse.
    #    - Status must be Accepted or Processing
    # 3. The CSMS sends a SetChargingProfileRequest
    #    Note(s): If NotifyEVChargingNeedsResponseStatus was Processing, the Test System will
    #    wait 60 seconds for the request
    #    - chargingProfilePurpose must be <TxProfile>
    #    - transactionId must be <Provided transactionId from before>
    # 4. The Test System responds with a SetChargingProfileResponse with status Accepted
    request = await negotiate_charging_schedule(
        cp, charging_needs(iso15118_version), max_schedule_tuples=2, evse_id=evse_id,
        session=session)

    # 5. The Test System sends a NotifyEVChargingScheduleRequest with evseId <Configured
    #    evseId> and chargingSchedule <ChargingSchedule provided at step 3>
    # 6. The CSMS responds with a NotifyEVChargingScheduleResponse.
    #    - status must be <Accepted>
    await notify_ev_charging_schedule(
        cp, request.charging_profile.charging_schedule[0], evse_id=evse_id,
        selected=iso15118_version == 'iso15118-20')

    # 7. The Test System sends a TransactionEventRequest with triggerReason
    #    <ChargingStateChanged> and transactionInfo.chargingState <Charging>
    # 8. The CSMS responds with a TransactionEventResponse.
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='ChargingStateChanged',
        seq_no=session.next_seq_no(),
        transaction_info={'transaction_id': session.transaction_id, 'charging_state': 'Charging'},
    ))
    session.state = 'EnergyTransferStarted'
    return request
