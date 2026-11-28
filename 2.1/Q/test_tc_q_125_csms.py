"""
Test case name      Idle operationMode - Idle, minimizing energy consumption - Idle with EvseSleep
Test case Id        TC_Q_125_CSMS
Use case Id(s)      Q10
Requirement(s)      Q10.FR.01

Requirement Details:
    Q10.FR.01: The fields limit, dischargeLimit, setpoint and setpointReactive SHALL be absent
        Precondition: When a chargingSchedulePeriod has operationMode = Idle
        Note: This also applies to the L2/L3 variants of these fields.
System under test   CSMS

Description         To request the EV to not perform any charging or discharging. Preconditioning of the
                    vehicle is allowed.

Purpose             To verify that the CSMS is able to send a Charging Profile which Minimizes the energy
                    consumption.

Prerequisite(s)     - CSMS supports ISO15118-20
                    - CS supports V2XChargingCtrlr.V2XSupportedOperationModes containing Idle
                    - CS supports SmartChargingCtrlr.SupportsFeature[EvseSleep] = true

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State ISO15118-20 transaction started in V2X AC_BPT energy transfer mode

Without EVSE sleeping

Manual Action: trigger CSMS to set a TxProfile Charging Profile with chargingSchedulePeriod with operationMode
               Idle and evseSleep false

2. The CSMS the sends a SetChargingProfileRequest
3. The Test System responds with a SetChargingProfileResponse with
    - status must be Accepted
4. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason OperationModeChanged
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.operationMode Idle
    - evseSleep false
5. The CSMS responds with a TransactionEventResponse

With EVSE sleeping

Manual Action: trigger CSMS to set a TxProfile Charging Profile with chargingSchedulePeriod with operationMode
               Idle and evseSleep true

6. The CSMS the sends a SetChargingProfileRequest
7. The Test System responds with a SetChargingProfileResponse
8. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason MeterValuePeriodic
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.operationMode Idle
    - evseSleep true
9. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose must be TxProfile
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.operationMode must be Idle
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.evseSleep must be false
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.dischargingLimit must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpoint must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpointReactive must be <omitted>
* Step 6:
    Message: SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose must be TxProfile
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.operationMode must be Idle
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.evseSleep must be true
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.dischargingLimit must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpoint must be <omitted>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.setpointReactive must be <omitted>

Post scenario validations:
    N/a

Remarks
The section heading for this test is printed as "TC_Q_125_CSMS: Idle operationMode - Idle, minimizing energy
consumption - Idle with EvseSleep", while the Test case Id row of the table is printed as "TC_Q_150_CS". The
test_case_id field holds the cell text as printed.
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.iso15118_20_transaction_just_started import V2X_VARIABLES
from reusable_states.iso15118_20_transaction_started_in_v2x_ac_bpt_energy_transfer_mode import (
    iso15118_20_transaction_started_in_v2x_ac_bpt_energy_transfer_mode,
)
from smart_charging import (
    only_schedule,
    request_charging_profile,
    tx_profile_id,
    v2x_profile,
    validate_profile,
)
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


def validate_idle_period(request, evse_sleep):
    """The tool validations of the SetChargingProfileRequests of this test case."""
    validate_profile(request, purpose='TxProfile', stack_level=None)
    period = only_schedule(request).charging_schedule_period[0]
    assert period.operation_mode == 'Idle', \
        f"Expected chargingSchedulePeriod.operationMode Idle, got {period.operation_mode}"
    # ChargingSchedulePeriodType.evseSleep: "Default value when absent is false"
    assert (period.evse_sleep or False) is evse_sleep, \
        f"Expected chargingSchedulePeriod.evseSleep {str(evse_sleep).lower()}, got {period.evse_sleep}"
    for name in ('limit', 'discharge_limit', 'setpoint', 'setpoint_reactive'):
        assert period[name] is None, f"chargingSchedulePeriod.{name} must be omitted, got {period[name]}"


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_q_125(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: CS supports V2XChargingCtrlr.SupportedOperationModes containing Idle, and
    # SmartChargingCtrlr.SupportsFeature[EvseSleep] = true
    cp.variables = dict(V2X_VARIABLES)
    cp.variables['SmartChargingCtrlr.SupportsFeature[EvseSleep]'] = 'true'
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State ISO15118-20 transaction started in V2X AC_BPT energy transfer
    #    mode
    _, transaction_id = await iso15118_20_transaction_started_in_v2x_ac_bpt_energy_transfer_mode(cp)
    # The TxProfiles of this test case replace the one that the transaction has (K01.FR.05,
    # K01.FR.39).
    profile_id = tx_profile_id(cp, transaction_id)

    # Without EVSE sleeping
    # Manual Action: trigger CSMS to set a TxProfile Charging Profile with chargingSchedulePeriod
    #                with operationMode Idle and evseSleep false
    # 2. The CSMS the sends a SetChargingProfileRequest
    # 3. The Test System responds with a SetChargingProfileResponse with
    #    - status must be Accepted
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, v2x_profile(
        'TxProfile', 'Absolute', {'operationMode': 'Idle', 'evseSleep': False},
        profile_id=profile_id, transactionId=transaction_id))
    validate_idle_period(request, evse_sleep=False)

    # 4. The Test System sends a TransactionEventRequest with
    #    - eventType Updated
    #    - triggerReason OperationModeChanged
    #    - transactionInfo.transactionId <transactionId>
    #    - transactionInfo.operationMode Idle
    #    - evseSleep false
    # 5. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='OperationModeChanged',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'operation_mode': 'Idle'},
        evse_sleep=False,
    ))

    # With EVSE sleeping
    # Manual Action: trigger CSMS to set a TxProfile Charging Profile with chargingSchedulePeriod
    #                with operationMode Idle and evseSleep true
    # 6. The CSMS the sends a SetChargingProfileRequest
    # 7. The Test System responds with a SetChargingProfileResponse
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, v2x_profile(
        'TxProfile', 'Absolute', {'operationMode': 'Idle', 'evseSleep': True},
        profile_id=profile_id, transactionId=transaction_id))
    validate_idle_period(request, evse_sleep=True)

    # 8. The Test System sends a TransactionEventRequest with
    #    - eventType Updated
    #    - triggerReason MeterValuePeriodic
    #    - transactionInfo.transactionId <transactionId>
    #    - transactionInfo.operationMode Idle
    #    - evseSleep true
    # 9. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='MeterValuePeriodic',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'operation_mode': 'Idle'},
        evse_sleep=True,
    ))

    start_task.cancel()
