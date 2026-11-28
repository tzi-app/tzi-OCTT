"""
Test case name      Local Cost Calculation - Change transaction tariff - TariffMaxElements
Test case Id        TC_I_113_CSMS
Use case Id(s)      I11
Requirement(s)      …
System under test   CSMS

Description         CSMS changes the tariff that is associated with a transaction. This may be needed when
                    dealing with unexpected price changes.

Purpose             To verify if the CSMS is able to process a response indicating TooManyElements.

Prerequisite(s)     - The CSMS supports local cost calculation by CS.
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. Execute Reusable State EnergyTransferStarted

Manual Action: Request the CSMS to change the tariff of the transaction

2. The CSMS sends a ChangeTransactionTariffRequest with
3. The Test System responds with ChangeTransactionTariffResponse with
    status TooManyElements

Tool validations
* Step 2:
    Message ChangeTransactionTariffRequest
    - transactionId must be <transaction id>

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from tariffs import energy_tariff, tariff_cost_ctrlr_variables
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_i_113(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: CS has TariffCostCtrlr.Enabled[Tariff] = true and MaxElements[Tariff] > 0
    cp.variables = tariff_cost_ctrlr_variables()
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Execute Reusable State EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # Manual Action: Request the CSMS to change the tariff of the transaction
    # 2. The CSMS sends a ChangeTransactionTariffRequest
    # 3. The Test System responds with ChangeTransactionTariffResponse with status
    #    TooManyElements
    cp.set_response('ChangeTransactionTariff', status='TooManyElements')
    request = await cp.wait_for_request(
        'ChangeTransactionTariff',
        manual_action=send_call(BASIC_AUTH_CP, 'ChangeTransactionTariff', {
            'transactionId': transaction_id,
            'tariff': energy_tariff(),
        }))
    assert request.transaction_id == transaction_id, \
        f"Expected ChangeTransactionTariffRequest.transactionId {transaction_id}, " \
        f"got {request.transaction_id}"

    start_task.cancel()
