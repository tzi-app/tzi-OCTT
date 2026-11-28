"""
Test case name      Local Cost Calculation - Cost Details of Transaction
Test case Id        TC_I_122_CSMS
Use case Id(s)      I12
Requirement(s)      …
System under test   CSMS

Description         Charging Station calculates cost of the transaction locally and returns a break-down of
                    the cost at end of the transaction for every charging period for which a different tariff
                    element was active. CSMS can use this to generate invoices or Charge Detail Records for
                    EMSPs.

Purpose             To verify if the CSMS is able to process the cost details sent by the Charging Station.

Prerequisite(s)     - The CSMS supports local cost calculation by CS.
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.Enabled[Cost] = true
                    - CS has TariffCtrlr.Enabled[RunningCost] = true
                    - CS has TariffCtrlr.Interval[Cost] = 30
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0
                    - CS has TariffCtrlr.ConditionsSupported[Tariff] = true

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: _Request the CSMS to set a default tariff on EVSE 0 with
- Price for energy with a taxRate
- Price for chargingTime with a taxRate
- Price for idleTime with a taxRate
- Price for fixedFee with a taxRate
- Price for minCost with a taxRate
- Price for maxCost with a taxRate

1. The CSMS sends a SetDefaultTariffRequest
2. The Test System responds with SetDefaultTariffResponse with status Accepted
3. Execute Reusable State EnergyTransferStarted
4. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason RunningCost
    - costDetails.failureToCalculate <omitted>
    - costDetails.failureReason <omitted>
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.typeOfCost NormalCost
    - costDetails.totalCost.reservation <omitted>
    - costDetails.totalCost.fixed.exclTax 15
    - costDetails.totalCost.fixed.inclTax 15.75
    - costDetails.totalCost.fixed.taxRates[0].type t5_0
    - costDetails.totalCost.fixed.taxRates[0].tax 5.0
    - costDetails.chargingPeriods[0].tariffId <SetDefaultTariffRequest.tariff.tariffId of step 1>
    - costDetails.chargingPeriods[0].startPeriod <txStartDateTime>
    - costDetails.chargingPeriods[0].dimensions[0].type ChargingTime
    - costDetails.chargingPeriods[0].dimensions[0].volume 15
    - costDetails.chargingPeriods[0].dimensions[1].type Energy
    - costDetails.chargingPeriods[0].dimensions[1].volume 12
5. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message SetDefaultTariffRequest
    - evseId 0
    - tariff.energy must be <not omitted>
    - tariff.energy.taxRates must be <not omitted>
    - tariff.chargingTime must be <not omitted>
    - tariff.chargingTime.taxRates must be <not omitted>
    - tariff.idleTime must be <not omitted>
    - tariff.idleTime.taxRates must be <not omitted>
    - tariff.fixedFee must be <not omitted>
    - tariff.fixedFee.taxRates must be <not omitted>
    - tariff.minCost must be <not omitted>
    - tariff.minCost.exclTax must be <not omitted>
    - tariff.minCost.inclTax must be <not omitted>
    - tariff.minCost.taxRates must be <not omitted>
    - tariff.maxCost must be <not omitted>
    - tariff.maxCost.exclTax must be <not omitted>
    - tariff.maxCost.inclTax must be <not omitted>
    - tariff.maxCost.taxRates must be <not omitted>

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
from tariffs import full_tariff, tariff_cost_ctrlr_variables, validate_full_tariff
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

# The tax of the fixed fee in the costDetails of the scenario: 5% of 15.00
TAX_RATE = {'type': 't5_0', 'tax': 5.0}


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_i_122(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: CS has TariffCostCtrlr.Enabled[Tariff] = true, Enabled[Cost] = true,
    # Enabled[RunningCost] = true, Interval[Cost] = 30, MaxElements[Tariff] > 0 and
    # ConditionsSupported[Tariff] = true
    cp.variables = tariff_cost_ctrlr_variables(Cost='true', RunningCost='true')
    cp.variables['TariffCostCtrlr.Interval[Cost]'] = '30'
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to set a default tariff on EVSE 0 with a price with a
    #     taxRate for energy, chargingTime, idleTime, fixedFee, minCost and maxCost
    # 1. The CSMS sends a SetDefaultTariffRequest
    # 2. The Test System responds with SetDefaultTariffResponse with status Accepted
    cp.set_response('SetDefaultTariff', status='Accepted')
    request = await cp.wait_for_request(
        'SetDefaultTariff',
        manual_action=send_call(BASIC_AUTH_CP, 'SetDefaultTariff', {
            'evseId': 0,
            'tariff': full_tariff(valid_from=False, fixed_fee=15.00, tax_rate=TAX_RATE),
        }))
    assert request.evse_id == 0, f"Expected SetDefaultTariffRequest.evseId 0, got {request.evse_id}"
    validate_full_tariff('SetDefaultTariffRequest', request.tariff, valid_from=False)

    # 3. Execute Reusable State EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)
    transaction_started_at = next(
        payload['timestamp'] for action, payload in cp.sent_requests
        if action == 'TransactionEvent' and payload['eventType'] == 'Started')

    # 4. The Test System sends a TransactionEventRequest with
    #    - eventType Updated
    #    - triggerReason RunningCost
    #    - costDetails.failureToCalculate <omitted>
    #    - costDetails.failureReason <omitted>
    #    - costDetails.totalCost.currency EUR
    #    - costDetails.totalCost.typeOfCost NormalCost
    #    - costDetails.totalCost.reservation <omitted>
    #    - costDetails.totalCost.fixed.exclTax 15
    #    - costDetails.totalCost.fixed.inclTax 15.75
    #    - costDetails.totalCost.fixed.taxRates[0].type t5_0
    #    - costDetails.totalCost.fixed.taxRates[0].tax 5.0
    #    - costDetails.chargingPeriods[0].tariffId <SetDefaultTariffRequest.tariff.tariffId of
    #      step 1>
    #    - costDetails.chargingPeriods[0].startPeriod <txStartDateTime>
    #    - costDetails.chargingPeriods[0].dimensions[0].type ChargingTime
    #    - costDetails.chargingPeriods[0].dimensions[0].volume 15
    #    - costDetails.chargingPeriods[0].dimensions[1].type Energy
    #    - costDetails.chargingPeriods[0].dimensions[1].volume 12
    #    The total and the totalUsage are required fields: the total is the fixed fee, the usage
    #    the 15 s of charging time and 12 Wh of energy of the charging period.
    # 5. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='RunningCost',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        cost_details={
            'total_cost': {
                'currency': 'EUR',
                'type_of_cost': 'NormalCost',
                'fixed': {'excl_tax': 15, 'incl_tax': 15.75, 'tax_rates': [TAX_RATE]},
                'total': {'excl_tax': 15, 'incl_tax': 15.75},
            },
            'total_usage': {'energy': 12, 'charging_time': 15, 'idle_time': 0},
            'charging_periods': [{
                'tariff_id': request.tariff.tariff_id,
                'start_period': transaction_started_at,
                'dimensions': [
                    {'type': 'ChargingTime', 'volume': 15},
                    {'type': 'Energy', 'volume': 12},
                ],
            }],
        },
    ))

    start_task.cancel()
