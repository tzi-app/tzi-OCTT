"""
Test case name      Transactions with fixed cost, energy or time - CS calculates costs and specifies limit
Test case Id        TC_E_108_CSMS
Use case Id(s)      E16
Requirement(s)      …
System under test   CSMS

Description         EV Driver or CSMS specifies a limit in cost, energy, state of charge or time for
                    transaction.

Purpose             To verify whether the CSMS correctly handles transactions where the Charging Station uses
                    local cost calculation and specifies a cost limit.

Prerequisite(s)     - Test System has TariffCostCtrlr.Enabled[Cost] is true
                    - Test System has TariffCostCtrlr.Enabled[RunningCost] is true

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger CSMS to configure a tariff with 1 EUR / minute for charging time

1. The CSMS sends a SetDefaultTariffRequest with
    - evseId 0
    - tariff.tariffId <not omitted>
    - tariff.currency EUR
    - tariff.chargingTime.prices[0].priceMinute 1.00
2. The Test System responds with a SetDefaultTariffResponse
3. Execute Reusable State EnergyTransferStarted
4. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason LimitSet
    - transactionInfo.transactionLimit.maxCost 2.00
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.typeOfCost NormalCost
    - costDetails.totalCost.chargingTime.inclTax 1.00
    - costDetails.totalCost.total.inclTax 1.00
    - costDetails.totalUsage.chargingTime 60
    - costDetails.totalUsage.idleTime <not omitted>
5. The CSMS responds with a TransactionEventResponse
6. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason RunningCost
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.typeOfCost NormalCost
    - costDetails.totalCost.chargingTime.inclTax 1.50
    - costDetails.totalCost.total.inclTax 1.50
    - costDetails.totalUsage.chargingTime 90
    - costDetails.totalUsage.idleTime <not omitted>
7. The CSMS responds with a TransactionEventResponse
8. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - triggerReason CostLimitReached
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.typeOfCost NormalCost
    - costDetails.totalCost.chargingTime.inclTax 2.00
    - costDetails.totalCost.total.inclTax 2.00
    - costDetails.totalUsage.chargingTime 120
    - costDetails.totalUsage.idleTime <not omitted>
9. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message: SetDefaultTariffRequest
    - evseId must be <evse id>
    - tariff.tariffId must be <not omitted>
    - tariff.currency must be EUR
    - tariff.chargingTime.prices[0].priceMinute must be 1.00
* Step 5:
    Message: TransactionEventResponse
    - totalCost must be <omitted>
    - transactionLimit must be <omitted>
* Step 7:
    Message: TransactionEventResponse
    - totalCost must be <omitted>
    - transactionLimit must be <omitted>
* Step 9:
    Message: TransactionEventResponse
    - totalCost must be <omitted>
    - transactionLimit must be <omitted>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


def cost_details(charging_time, cost):
    """The costDetails of the local cost calculation, with the tariff of 1 EUR per minute of
    charging time: the cost after charging_time seconds."""
    return {
        'total_cost': {
            'currency': 'EUR',
            'type_of_cost': 'NormalCost',
            'charging_time': {'incl_tax': cost},
            'total': {'incl_tax': cost},
        },
        'total_usage': {
            # 11 kW during the charging time, in Wh
            'energy': round(11000 * charging_time / 3600),
            'charging_time': charging_time,
            'idle_time': 0,
        },
    }


def validate_response(response):
    assert response.total_cost is None, \
        f"TransactionEventResponse.totalCost must be omitted, got {response.total_cost}"
    assert response.transaction_limit is None, \
        f"TransactionEventResponse.transactionLimit must be omitted, got {response.transaction_limit}"


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_108(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: Test System has TariffCostCtrlr.Enabled[Cost] is true and
    # TariffCostCtrlr.Enabled[RunningCost] is true
    cp.variables = {
        'TariffCostCtrlr.Enabled[Cost]': 'true',
        'TariffCostCtrlr.Enabled[RunningCost]': 'true',
    }
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Trigger CSMS to configure a tariff with 1 EUR / minute for charging time
    # 1. The CSMS sends a SetDefaultTariffRequest with
    #    - evseId 0
    #    - tariff.tariffId <not omitted>
    #    - tariff.currency EUR
    #    - tariff.chargingTime.prices[0].priceMinute 1.00
    # 2. The Test System responds with a SetDefaultTariffResponse
    request = await cp.wait_for_request(
        'SetDefaultTariff',
        manual_action=send_call(BASIC_AUTH_CP, 'SetDefaultTariff', {
            'evseId': 0,
            'tariff': {
                'tariffId': 'charging-time-1-eur-per-minute',
                'currency': 'EUR',
                'chargingTime': {'prices': [{'priceMinute': 1.00}]},
            },
        }))
    assert request.evse_id == 0, f"Expected SetDefaultTariffRequest.evseId 0, got {request.evse_id}"
    assert request.tariff.tariff_id, "SetDefaultTariffRequest.tariff.tariffId must not be omitted"
    assert request.tariff.currency == 'EUR', \
        f"Expected SetDefaultTariffRequest.tariff.currency EUR, got {request.tariff.currency}"
    assert request.tariff.charging_time is not None, \
        "SetDefaultTariffRequest.tariff has no chargingTime"
    assert request.tariff.charging_time.prices[0].price_minute == 1.00, \
        f"Expected tariff.chargingTime.prices[0].priceMinute 1.00, " \
        f"got {request.tariff.charging_time.prices[0].price_minute}"

    # 3. Execute Reusable State EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # 4. The Test System sends a TransactionEventRequest with
    #    - eventType Updated
    #    - triggerReason LimitSet
    #    - transactionInfo.transactionLimit.maxCost 2.00
    #    - costDetails.totalCost.currency EUR
    #    - costDetails.totalCost.typeOfCost NormalCost
    #    - costDetails.totalCost.chargingTime.inclTax 1.00
    #    - costDetails.totalCost.total.inclTax 1.00
    #    - costDetails.totalUsage.chargingTime 60
    #    - costDetails.totalUsage.idleTime <not omitted>
    # 5. The CSMS responds with a TransactionEventResponse
    response = await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='LimitSet',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'transaction_limit': {'max_cost': 2.00}},
        cost_details=cost_details(charging_time=60, cost=1.00),
    ))
    validate_response(response)

    # 6. The Test System sends a TransactionEventRequest with
    #    - eventType Updated
    #    - triggerReason RunningCost
    #    - costDetails.totalCost.currency EUR
    #    - costDetails.totalCost.typeOfCost NormalCost
    #    - costDetails.totalCost.chargingTime.inclTax 1.50
    #    - costDetails.totalCost.total.inclTax 1.50
    #    - costDetails.totalUsage.chargingTime 90
    #    - costDetails.totalUsage.idleTime <not omitted>
    # 7. The CSMS responds with a TransactionEventResponse
    response = await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='RunningCost',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        cost_details=cost_details(charging_time=90, cost=1.50),
    ))
    validate_response(response)

    # 8. The Test System sends a TransactionEventRequest with
    #    - eventType Ended
    #    - triggerReason CostLimitReached
    #    - costDetails.totalCost.currency EUR
    #    - costDetails.totalCost.typeOfCost NormalCost
    #    - costDetails.totalCost.chargingTime.inclTax 2.00
    #    - costDetails.totalCost.total.inclTax 2.00
    #    - costDetails.totalUsage.chargingTime 120
    #    - costDetails.totalUsage.idleTime <not omitted>
    # 9. The CSMS responds with a TransactionEventResponse
    response = await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='CostLimitReached',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        cost_details=cost_details(charging_time=120, cost=2.00),
    ))
    validate_response(response)

    start_task.cancel()
