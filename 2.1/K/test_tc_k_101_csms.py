"""
Test case name      Set Charging Profile - Change operation mode
Test case Id        TC_K_101_CSMS
Use case Id(s)      K01
Requirement(s)      …
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs.

Purpose             To verify if the CSMS is able to handle the message that the Charging Station sends when a
                    charging profile changes the operationMode of a transaction.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      State is ISO15118-20 transaction started in V2X AC_BPT energy transfer mode

Test Scenario
Manual Action: Request the CSMS to send a TxDefaultProfile charging profile with operationMode Idle

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with
    - status Accepted
3. The Test System sends a TransactionEventRequest with
    - eventType _Updated
    - triggerReason OperationModeChanged
    - transactionInfo.operationMode Idle
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose must be TxDefaultProfile
    - chargingProfile.chargingSchedule.chargingSchedulePeriod[0].operationMode must be Idle
* Step 4:
    Message: TransactionEventResponse
    - status must be Accepted

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.14. Page 334 - (2026-09) - K01 - added missing requirement to reject ExternalConstraints from CSMS
        [1327]
        (Part 2 errata - applies to this test via use case K01)
        A CSMS is forbidden to send a ChargingStationExternalConstraints profile to a charging station, but a
        matching requirement that Charging Station must reject it if it receives such a charging profile was
        missing.

        New requirement

        | ID | Precondition | Requirement definition | Note |
        | K01.FR.62 | When a Charging Station receives a SetChargingProfileRequest from CSMS with
          chargingProfilePurpose set to ChargingStationExternalConstraints | Charging Station SHALL respond
          with a status = Rejected and optionally a statusInfo.reasonCode = UnsupportedPurpose | Purpose not
          allowed from CSMS. |

    2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] -
        2.16.2. Page 334 - Set Charging Profile
        (Part 2 errata - applies to this test via use case K01)
        Added a requirement that CSMS shall not send a LocalGeneration profile and a requirement that a
        Charging Station shall reject it.

        New requirements

        | ID | Precondition | Requirement definition | Note |
        | K01.FR.63 / (2.1) | | The CSMS SHALL NOT set chargingProfilePurpose to LocalGeneration in a
          SetChargingProfileRequest. | This purpose is only received from an external system. |
        | K01.FR.64 / (2.1) | When a Charging Station receives a SetChargingProfileRequest from CSMS with
          chargingProfilePurpose set to LocalGeneration | Charging Station SHALL respond with a status =
          Rejected and optionally a statusInfo.reasonCode = UnsupportedPurpose | Purpose not allowed from
          CSMS. |
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
from smart_charging import charging_profile, request_charging_profile, validate_profile
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_101(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # The Test System supports ISO 15118-20 and V2X.
    cp.variables = dict(V2X_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is ISO15118-20 transaction started in V2X AC_BPT energy transfer mode
    _, transaction_id = await iso15118_20_transaction_started_in_v2x_ac_bpt_energy_transfer_mode(cp)

    # Manual Action: Request the CSMS to send a TxDefaultProfile charging profile with
    #                operationMode Idle
    # 1. The CSMS sends a SetChargingProfileRequest
    # 2. The Test System responds with a SetChargingProfileResponse with
    #    - status Accepted
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, charging_profile(
        'TxDefaultProfile', 'Absolute', 0,
        schedule={'chargingSchedulePeriod': [{'startPeriod': 0, 'operationMode': 'Idle'}]}))
    validate_profile(request, purpose='TxDefaultProfile', stack_level=None)
    period = request.charging_profile.charging_schedule[0].charging_schedule_period[0]
    assert period.operation_mode == 'Idle', \
        f"Expected chargingSchedule.chargingSchedulePeriod[0].operationMode Idle, got {period.operation_mode}"

    # 3. The Test System sends a TransactionEventRequest with
    #    - eventType Updated
    #    - triggerReason OperationModeChanged
    #    - transactionInfo.operationMode Idle
    # 4. The CSMS responds with a TransactionEventResponse: it accepts the event
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='OperationModeChanged',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'operation_mode': 'Idle'},
    ))

    start_task.cancel()
