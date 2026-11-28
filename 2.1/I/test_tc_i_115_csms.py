"""
Test case name      Local Cost Calculation - Change transaction tariff - TariffConditionsSupported is true
Test case Id        TC_I_115_CSMS
Use case Id(s)      I11
Requirement(s)      …
System under test   CSMS

Description         CSMS changes the tariff that is associated with a transaction. This may be needed when
                    dealing with unexpected price changes.

Purpose             To verify if the CSMS is able to change the tariff of a transaction with a tariff with
                    conditions.

Prerequisite(s)     - The CSMS supports local cost calculation by CS.
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0
                    - CS has TariffCtrlr.ConditionsSupported[Tariff] = true

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. Execute Reusable State EnergyTransferStarted

Manual Action: Request the CSMS to change the tariff of the transaction with
- validFrom
- Price for energy with condition on startTimeOfDay and endTimeOfDay

2. The CSMS sends a ChangeTransactionTariffRequest with
3. The Test System responds with ChangeTransactionTariffResponse with
    - status Accepted

Tool validations
* Step 2:
    Message ChangeTransactionTariffRequest
    - transactionId must be <transaction id>
    - tariff.validFrom must be <not omitted>
    - tariff.energy.prices[0].priceKwh must be <not omitted>
    - tariff.energy.prices[0].conditions.startTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute
    - tariff.energy.prices[0].conditions.endTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute

Post scenario validations:
    N/a

Remarks
Section heading as printed: "TC_I_115_CSMS: Local Cost Calculation - Change transaction tariff - Good flow"
                            (differs from the Test case name cell). The Requirement(s) cell is printed as "…"
                            only, with no requirement codes. Step 2 is printed ending in "with" and no
                            parameters follow it in the scenario.
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from tariffs import tariff_cost_ctrlr_variables, time_of_day_tariff, validate_time_of_day_prices
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_i_115(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: CS has TariffCostCtrlr.Enabled[Tariff] = true, MaxElements[Tariff] > 0 and
    # ConditionsSupported[Tariff] = true
    cp.variables = tariff_cost_ctrlr_variables()
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # Manual Action: Request the CSMS to change the tariff of the transaction with
    #     - validFrom
    #     - Price for energy with condition on startTimeOfDay and endTimeOfDay
    # 2. The CSMS sends a ChangeTransactionTariffRequest
    # 3. The Test System responds with ChangeTransactionTariffResponse with
    #    - status Accepted
    cp.set_response('ChangeTransactionTariff', status='Accepted')
    request = await cp.wait_for_request(
        'ChangeTransactionTariff',
        manual_action=send_call(BASIC_AUTH_CP, 'ChangeTransactionTariff', {
            'transactionId': transaction_id,
            'tariff': time_of_day_tariff([('08:00', '20:00', 0.40)]),
        }))
    assert request.transaction_id == transaction_id, \
        f"Expected ChangeTransactionTariffRequest.transactionId {transaction_id}, " \
        f"got {request.transaction_id}"
    validate_time_of_day_prices('ChangeTransactionTariffRequest', request.tariff)

    start_task.cancel()
