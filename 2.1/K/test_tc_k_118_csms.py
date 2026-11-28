"""
Test case name      Priority Charging - Requesting priority charging remotely
Test case Id        TC_K_118_CSMS
Use case Id(s)      K21
Requirement(s)      K21.FR.09, K21.FR.10

Requirement Details:
    K21.FR.09: CSMS SHALL respond with NotifyPriorityChargingResponse.
        Precondition: K21.FR.05 OR K21.FR.08
    K21.FR.10: CSMS SHALL support sending a UsePriorityChargingRequest
        Note: A Charging Station reports support for this in SmartChargingCtrlr.SupportedAdditionalPurposes.
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify the CSMS supports priority charging initiated from CSMS.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to use priority charging for the transaction

1. The CSMS sends a UsePriorityChargingRequest
2. The Test System responds with a UsePriorityChargingResponse with
    - status Accepted
3. The Test System sends a NotifyPriorityChargingRequest with
    - transactionId <transactionId>
    - activated true
4. The CSMS responds with a NotifyPriorityChargingResponse

Tool validations
* Step 1:
    Message: UsePriorityChargingRequest
    - transactionId must be <transactionId>
    - activate true

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_118(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # The Test System supports priority charging.
    cp.variables = {'SmartChargingCtrlr.SupportedAdditionalPurposes': 'PriorityCharging'}
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # Manual Action: Request the CSMS to use priority charging for the transaction
    # 1. The CSMS sends a UsePriorityChargingRequest
    # 2. The Test System responds with a UsePriorityChargingResponse with
    #    - status Accepted
    cp.set_response('UsePriorityCharging', status='Accepted')
    request = await cp.wait_for_request(
        'UsePriorityCharging',
        manual_action=send_call(BASIC_AUTH_CP, 'UsePriorityCharging', {
            'transactionId': transaction_id,
            'activate': True,
        }))
    assert request.transaction_id == transaction_id, \
        f"Expected UsePriorityChargingRequest.transactionId {transaction_id}, got {request.transaction_id}"
    assert request.activate is True, \
        f"Expected UsePriorityChargingRequest.activate true, got {request.activate}"

    # 3. The Test System sends a NotifyPriorityChargingRequest with
    #    - transactionId <transactionId>
    #    - activated true
    # 4. The CSMS responds with a NotifyPriorityChargingResponse
    await cp.call(call.NotifyPriorityCharging(transaction_id=transaction_id, activated=True))

    start_task.cancel()
