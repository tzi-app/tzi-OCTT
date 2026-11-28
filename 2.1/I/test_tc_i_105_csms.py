"""
Test case name      Set Default Tariff - TariffConditionsSupported is false
Test case Id        TC_I_105_CSMS
Use case Id(s)      I07
Requirement(s)      …
System under test   CSMS

Description         To set the default tariff on the charging station, for example for ad hoc charging, or
                    when there is no driver-specific tariff.

Purpose             To verify if the CSMS is able to process a response indicating ConditionNotSupported.

Prerequisite(s)     - The CSMS supports local cost calculation by CS
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0
                    - CS has TariffCtrlr.ConditionsSupported[Tariff] = true

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: _Request the CSMS to set a default tariff on EVSE 0 with
- validFrom
- Price for energy in peak hours
- Price for energy other hours

1. The CSMS sends a SetDefaultTariffRequest
2. The Test System responds with SetDefaultTariffResponse with status ConditionsNotSupported

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
    - tariff.energy.prices[1].priceKwh must be <not omitted>
    - tariff.energy.prices[1].conditions.startTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute
    - tariff.energy.prices[1].conditions.endTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from tariffs import (
    PEAK_AND_OTHER_HOURS,
    tariff_cost_ctrlr_variables,
    time_of_day_tariff,
    validate_time_of_day_prices,
)
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_i_105(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: CS has TariffCostCtrlr.Enabled[Tariff] = true, MaxElements[Tariff] > 0 and
    # ConditionsSupported[Tariff] = true
    cp.variables = tariff_cost_ctrlr_variables()
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to set a default tariff on EVSE 0 with
    #     - validFrom
    #     - Price for energy in peak hours
    #     - Price for energy other hours
    # 1. The CSMS sends a SetDefaultTariffRequest
    # 2. The Test System responds with SetDefaultTariffResponse with status
    #    ConditionNotSupported
    cp.set_response('SetDefaultTariff', status='ConditionNotSupported')
    request = await cp.wait_for_request(
        'SetDefaultTariff',
        manual_action=send_call(BASIC_AUTH_CP, 'SetDefaultTariff', {
            'evseId': 0,
            'tariff': time_of_day_tariff(PEAK_AND_OTHER_HOURS),
        }))
    assert request.evse_id == 0, f"Expected SetDefaultTariffRequest.evseId 0, got {request.evse_id}"
    validate_time_of_day_prices('SetDefaultTariffRequest', request.tariff, number_of_prices=2)

    start_task.cancel()
