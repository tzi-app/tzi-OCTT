"""
Test case name      Clear Tariffs - DefaultTariff
Test case Id        TC_I_110_CSMS
Use case Id(s)      I10
Requirement(s)      …
System under test   Charging Station

Description         To clear previously set tariffs on the charging station.

Purpose             To verify if the CSMS is able to clear tariffs.

Prerequisite(s)     - The CSMS supports local cost calculation by CS
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to set a default tariff on EVSE 0.

1. The CSMS sends a SetDefaultTariffRequest
2. The Test System responds with SetDefaultTariffResponse with status Accepted

Manual Action: Request the CSMS to clear only the tariff set in step 1.

3. The CSMS sends a ClearTariffsRequest
4. The Test System responds with ClearTariffsResponse with
    - clearTariffsResult[0].tariffId <SetDefaultTariffRequest.tariff.tariffId of step 1>
    - clearTariffsResult[0].status Accepted

Manual Action: Request the CSMS to clear all tariffs.

5. The CSMS sends a ClearTariffsRequest
6. The Test System responds with ClearTariffsResponse with
    - clearTariffsResult[0].tariffId <omitted>
    - clearTariffsResult[0].status NoTariff

Tool validations
* Step 1:
    Message SetDefaultTariffRequest
    - evseId 0
    - tariff.tariffId must be <not omitted>
* Step 3:
    Message ClearTariffsRequest
    - tariffIds[0] must be _<SetDefaultTariffRequest.tariff.tariffId of step 1>
* Step 5:
    Message ClearTariffsRequest
    - tariffIds must be <omitted>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from tariffs import energy_tariff, tariff_cost_ctrlr_variables
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_i_110(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: CS has TariffCostCtrlr.Enabled[Tariff] = true and MaxElements[Tariff] > 0
    cp.variables = tariff_cost_ctrlr_variables()
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to set a default tariff on EVSE 0.
    # 1. The CSMS sends a SetDefaultTariffRequest
    # 2. The Test System responds with SetDefaultTariffResponse with status Accepted
    cp.set_response('SetDefaultTariff', status='Accepted')
    set_default_tariff = await cp.wait_for_request(
        'SetDefaultTariff',
        manual_action=send_call(BASIC_AUTH_CP, 'SetDefaultTariff', {
            'evseId': 0,
            'tariff': energy_tariff(),
        }))
    assert set_default_tariff.evse_id == 0, \
        f"Expected SetDefaultTariffRequest.evseId 0, got {set_default_tariff.evse_id}"
    tariff_id = set_default_tariff.tariff.tariff_id
    assert tariff_id, "SetDefaultTariffRequest.tariff.tariffId must not be omitted"

    # Manual Action: Request the CSMS to clear only the tariff set in step 1.
    # 3. The CSMS sends a ClearTariffsRequest
    # 4. The Test System responds with ClearTariffsResponse with
    #    - clearTariffsResult[0].tariffId <SetDefaultTariffRequest.tariff.tariffId of step 1>
    #    - clearTariffsResult[0].status Accepted
    cp.set_response('ClearTariffs', clear_tariffs_result=[{'tariff_id': tariff_id, 'status': 'Accepted'}])
    request = await cp.wait_for_request(
        'ClearTariffs',
        manual_action=send_call(BASIC_AUTH_CP, 'ClearTariffs', {'tariffIds': [tariff_id]}))
    assert request.tariff_ids and request.tariff_ids[0] == tariff_id, \
        f"Expected ClearTariffsRequest.tariffIds[0] {tariff_id}, got {request.tariff_ids}"

    # Manual Action: Request the CSMS to clear all tariffs.
    # 5. The CSMS sends a ClearTariffsRequest
    # 6. The Test System responds with ClearTariffsResponse with
    #    - clearTariffsResult[0].tariffId <omitted>
    #    - clearTariffsResult[0].status NoTariff
    cp.set_response('ClearTariffs', clear_tariffs_result=[{'status': 'NoTariff'}])
    request = await cp.wait_for_request(
        'ClearTariffs', manual_action=send_call(BASIC_AUTH_CP, 'ClearTariffs', {}))
    assert request.tariff_ids is None, \
        f"ClearTariffsRequest.tariffIds must be omitted, got {request.tariff_ids}"

    start_task.cancel()
