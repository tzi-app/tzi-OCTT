"""
Test case name      Set Default Tariff - startTimeOfDay, endTimeOfDay
Test case Id        TC_I_101_CSMS
Use case Id(s)      I07, I12
Requirement(s)      …
System under test   CSMS

Description         To set the default tariff on the charging station, for example for ad hoc charging, or
                    when there is no driver-specific tariff.

Purpose             To verify if the CSMS is able to set a tariff with conditions.

Prerequisite(s)     - The CSMS supports local cost calculation by CS
                    - The CSMS supports conditions in Tariffs
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0
                    - CS has TariffCtrlr.ConditionsSupported[Tariff] = true

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to set a default tariff on EVSE 0 with
- validFrom
- Price for energy with condition on startTimeOfDay and endTimeOfDay

1. The CSMS sends a SetDefaultTariffRequest
2. The Test System responds with SetDefaultTariffResponse with status Accepted

Tool validations
* Step 1:
    Message SetDefaultTariffRequest
    - evseId 0
    - tariff.validFrom must be <not omitted>
    - tariff.energy.prices[0].priceKwh must be <not omitted>
    - tariff.energy.prices[0].conditions.startTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute
    - tariff.energy.prices[0].conditions.endTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from tariffs import tariff_cost_ctrlr_variables, time_of_day_tariff, validate_time_of_day_prices
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_i_101(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: CS has TariffCostCtrlr.Enabled[Tariff] = true, MaxElements[Tariff] > 0 and
    # ConditionsSupported[Tariff] = true
    cp.variables = tariff_cost_ctrlr_variables()
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to set a default tariff on EVSE 0 with
    #     - validFrom
    #     - Price for energy with condition on startTimeOfDay and endTimeOfDay
    # 1. The CSMS sends a SetDefaultTariffRequest
    # 2. The Test System responds with SetDefaultTariffResponse with status Accepted
    cp.set_response('SetDefaultTariff', status='Accepted')
    request = await cp.wait_for_request(
        'SetDefaultTariff',
        manual_action=send_call(BASIC_AUTH_CP, 'SetDefaultTariff', {
            'evseId': 0,
            'tariff': time_of_day_tariff([('08:00', '20:00', 0.40)]),
        }))
    assert request.evse_id == 0, f"Expected SetDefaultTariffRequest.evseId 0, got {request.evse_id}"
    validate_time_of_day_prices('SetDefaultTariffRequest', request.tariff)

    start_task.cancel()
