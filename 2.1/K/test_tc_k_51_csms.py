"""
Test case name      EMS Control - Reset / release external charging limit - With ongoing transaction
Test case Id        TC_K_51_CSMS
Use case Id(s)      K13
Requirement(s)      N/a
System under test   CSMS

Description         A charging schedule or charging limit can be removed by an external system on the Charging
                    Station. An external control system sends a signal to release a previously imposed
                    charging limit to a Charging Station. The Charging Station notifies the CSMS about this.

Purpose             To verify if the CSMS is able to receive the notify from a charging station and respond
                    correctly as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System sends a ClearedChargingLimitRequest with
    - chargingLimitSource EMS
2. The CSMS responds with a ClearedChargingLimitResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason ChargingRateChanged
4. The CSMS responds with a TransactionEventResponse

Tool validations
- N/a

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_51(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # 1. The Test System sends a ClearedChargingLimitRequest with
    #    - chargingLimitSource EMS
    # 2. The CSMS responds with a ClearedChargingLimitResponse
    await cp.call(call.ClearedChargingLimit(charging_limit_source='EMS'))

    # 3. The Test System sends a TransactionEventRequest with
    #    - eventType Updated
    #    - triggerReason ChargingRateChanged
    # 4. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='ChargingRateChanged',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
    ))

    start_task.cancel()
