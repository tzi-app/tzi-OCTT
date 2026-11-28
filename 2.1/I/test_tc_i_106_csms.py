"""
Test case name      Set Default Tariff - validations
Test case Id        TC_I_106_CSMS
Use case Id(s)      I07, I09
Requirement(s)      …
System under test   CSMS

Description         To set the default tariff on the charging station, for example for ad hoc charging, or
                    when there is no driver-specific tariff.

Purpose             To verify if the CSMS supports configuring setting local cost calculation.

Prerequisite(s)     - The CSMS supports local cost calculation by CS
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0
                    - CS has TariffCtrlr.ConditionsSupported[Tariff] = true

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to set a default tariff on EVSE 0 with
- validFrom
- Price for energy with a taxRate
- Price for chargingTime with a taxRate
- Price for idleTime with a taxRate
- Price for fixedFee with a taxRate
- Price for minCost with a taxRate
- Price for maxCost with a taxRate
- Price for reservationTime with a taxRate

1. The CSMS sends a SetDefaultTariffRequest
2. The Test System responds with SetDefaultTariffResponse with status Accepted

Manual Action: Request the CSMS to set a default tariff on EVSE 1 with
- validFrom
- Price for energy with a taxRate
- Price for chargingTime with a taxRate
- Price for idleTime with a taxRate
- Price for fixedFee with a taxRate
- Price for minCost with a taxRate
- Price for maxCost with a taxRate
- Price for reservationFixed with a taxRate

3. The CSMS sends a SetDefaultTariffRequest with
4. The Test System responds with SetDefaultTariffResponse with status Accepted

Manual Action: Request the CSMS to get the tariffs for EVSE 0

5. The CSMS sends a GetTariffsRequest
6. The Test System responds with GetTariffsResponse with
    - status Accepted
    - tariffAssignments[0].tariffId <value of tariffId from step 1>
    - tariffAssignments[0].tariffKind DefaultTariff
    - tariffAssignments[0].evseIds [ 2 ]
    - tariffAssignments[0].validFrom must be <not omitted>
    - tariffAssignments[1].tariffId <value of tariffId from step 3>
    - tariffAssignments[1].tariffKind DefaultTariff
    - tariffAssignments[1].evseIds [ 1 ]
    - tariffAssignments[1].validFrom must be <not omitted>

Tool validations
* Step 1:
    Message SetDefaultTariffRequest
    - evseId 0
    - tariff.tariffId must be <not omitted>
    - tariff.validFrom must be _<not omitted>
    - tariff.energy must be <not omitted>
    - tariff.energy.taxRates must be <not omitted>
    - tariff.chargingTime must be <not omitted>
    - tariff.chargingTime.taxRates must be <not omitted>
    - tariff.idleTime must be <not omitted>
    - tariff.idleTime.taxRates must be <not omitted>
    - tariff.fixedFee must be <not omitted>
    - tariff.fixedFee.taxRates must be <not omitted>
    - tariff.minCost must be <not omitted>
    - tariff.minCost.exclTax or tariff.minCost.inclTax must be <not omitted> (at least one must exist)
    - tariff.minCost.taxRates must be <not omitted>
    - tariff.maxCost must be <not omitted>
    - tariff.maxCost.exclTax or tariff.maxCost.inclTax must be <not omitted> (at least one must exist)
    - tariff.maxCost.taxRates must be <not omitted>
    - tariff.reservationTime must be <not omitted>
    - tariff.reservationTime.taxRates must be <not omitted>
* Step 3:
    Message SetDefaultTariffRequest
    - evseId 1
    - tariff.tariffId must be <Different from tariffId step 1>
    - tariff.validFrom must be _<not omitted>
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
    - tariff.reservationFixed must be <not omitted>
    - tariff.reservationFixed.taxRates must be <not omitted>
* Step 5:
    Message GetTariffsRequest
    - evseId must be 0

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from tariffs import full_tariff, tariff_cost_ctrlr_variables, validate_full_tariff
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_i_106(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: CS has TariffCostCtrlr.Enabled[Tariff] = true, MaxElements[Tariff] > 0 and
    # ConditionsSupported[Tariff] = true
    cp.variables = tariff_cost_ctrlr_variables()
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to set a default tariff on EVSE 0 with validFrom and a
    #     price with a taxRate for energy, chargingTime, idleTime, fixedFee, minCost, maxCost
    #     and reservationTime
    # 1. The CSMS sends a SetDefaultTariffRequest
    # 2. The Test System responds with SetDefaultTariffResponse with status Accepted
    cp.set_response('SetDefaultTariff', status='Accepted')
    first = await cp.wait_for_request(
        'SetDefaultTariff',
        manual_action=send_call(BASIC_AUTH_CP, 'SetDefaultTariff', {
            'evseId': 0,
            'tariff': full_tariff(reservation='reservationTime'),
        }))
    assert first.evse_id == 0, f"Expected SetDefaultTariffRequest.evseId 0, got {first.evse_id}"
    # minCost and maxCost: exclTax or inclTax must be there (at least one must exist)
    validate_full_tariff('SetDefaultTariffRequest', first.tariff, reservation='reservationTime',
                         excl_and_incl_tax=False)

    # Manual Action: Request the CSMS to set a default tariff on EVSE 1 with validFrom and a
    #     price with a taxRate for energy, chargingTime, idleTime, fixedFee, minCost, maxCost
    #     and reservationFixed
    # 3. The CSMS sends a SetDefaultTariffRequest
    # 4. The Test System responds with SetDefaultTariffResponse with status Accepted
    second = await cp.wait_for_request(
        'SetDefaultTariff',
        manual_action=send_call(BASIC_AUTH_CP, 'SetDefaultTariff', {
            'evseId': 1,
            'tariff': full_tariff(reservation='reservationFixed'),
        }))
    assert second.evse_id == 1, f"Expected SetDefaultTariffRequest.evseId 1, got {second.evse_id}"
    assert second.tariff.tariff_id != first.tariff.tariff_id, \
        f"The tariffId of step 3 must be different from the one of step 1: {second.tariff.tariff_id}"
    validate_full_tariff('SetDefaultTariffRequest', second.tariff, reservation='reservationFixed')

    # Manual Action: Request the CSMS to get the tariffs for EVSE 0
    # 5. The CSMS sends a GetTariffsRequest
    # 6. The Test System responds with GetTariffsResponse with
    #    - status Accepted
    #    - tariffAssignments[0].tariffId <value of tariffId from step 1>
    #    - tariffAssignments[0].tariffKind DefaultTariff
    #    - tariffAssignments[0].evseIds [ 2 ]
    #    - tariffAssignments[0].validFrom must be <not omitted>
    #    - tariffAssignments[1].tariffId <value of tariffId from step 3>
    #    - tariffAssignments[1].tariffKind DefaultTariff
    #    - tariffAssignments[1].evseIds [ 1 ]
    #    - tariffAssignments[1].validFrom must be <not omitted>
    cp.set_response('GetTariffs', status='Accepted', tariff_assignments=[
        {
            'tariff_id': first.tariff.tariff_id,
            'tariff_kind': 'DefaultTariff',
            'evse_ids': [2],
            'valid_from': first.tariff.valid_from,
        },
        {
            'tariff_id': second.tariff.tariff_id,
            'tariff_kind': 'DefaultTariff',
            'evse_ids': [1],
            'valid_from': second.tariff.valid_from,
        },
    ])
    request = await cp.wait_for_request(
        'GetTariffs', manual_action=send_call(BASIC_AUTH_CP, 'GetTariffs', {'evseId': 0}))
    assert request.evse_id == 0, f"Expected GetTariffsRequest.evseId 0, got {request.evse_id}"

    start_task.cancel()
