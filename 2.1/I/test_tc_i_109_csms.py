"""
Test case name      Receive Driver Tariff - Goodflow
Test case Id        TC_I_109_CSMS
Use case Id(s)      I08
Requirement(s)      I08.FR.01

Requirement Details:
    I08.FR.01: CSMS SHALL respond with an AuthorizeResponse with a tariff field and any other relevant fields
               (like idTokenInfo).
        Precondition: When CSMS receives an AuthorizeRequest for an idToken that is accepted for charging and
                      for which a driver-specific tariff exists
        Note: The details of the authorization process are described in chapter C. Authorization.
System under test   CSMS

Description         To support receiving the driver-specific tariff to enable local cost calculation based on
                    a tariff for this driver.

Purpose             To verify if the CSMS supports driver tariffs.

Prerequisite(s)     - The CSMS supports local cost calculation by CS
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0

Configuration State CSMS is configured to provide a driver specific tariff for <Configured
                    valid_idtoken_idtoken> that specifies:
                    - currency: <not omitted>
                    - energy price: 0.25 per kWh (ex VAT), vat 20%
                    - idle price: 0.10 per minute (ex VAT), vat 20%
                    - fixed fee: 0.50 (ex VAT), vat 20%

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured valid_idtoken_idtoken>
2. The CSMS responds with AuthorizeResponse

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status must be Accepted
    - tariff.tariffId must be <not omitted>
    - tariff.currency must be <not omitted>
    - tariff.energy.prices[0].priceKwh must be 0.25
    - tariff.energy.taxRates[0].tax must be 20
    - tariff.energy.taxRates[0].type must be VAT
    - tariff.idleTime.prices[0].priceMinute must be 0.10
    - tariff.idleTime.taxRates[0].tax must be 20
    - tariff.idleTime.taxRates[0].type must be VAT
    - tariff.fixedFee.prices[0].priceFixed must be 0.50
    - tariff.fixedFee.taxRates[0].tax must be 20
    - tariff.fixedFee.taxRates[0].type must be VAT

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import TziChargePoint21
from reusable_states.booted import booted
from tariffs import new_tariff_id, tariff_cost_ctrlr_variables, VAT
from trigger import set_driver_tariff
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']


def validate_price(tariff, element, price_field, price):
    """A price of the driver tariff, excluding VAT, and its VAT of 20%."""
    part = tariff[element]
    name = ''.join(word.capitalize() if index else word
                   for index, word in enumerate(element.split('_')))
    assert part is not None, f"AuthorizeResponse.tariff has no {name}"
    assert part.prices[0][price_field] == price, \
        f"Expected AuthorizeResponse.tariff.{name}.prices[0] {price}, got {part.prices[0]}"
    assert part.tax_rates, f"AuthorizeResponse.tariff.{name} has no taxRates"
    assert part.tax_rates[0].tax == 20, \
        f"Expected AuthorizeResponse.tariff.{name}.taxRates[0].tax 20, got {part.tax_rates[0].tax}"
    assert part.tax_rates[0].type == 'VAT', \
        f"Expected AuthorizeResponse.tariff.{name}.taxRates[0].type VAT, got {part.tax_rates[0].type}"


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_i_109(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites: CS has TariffCostCtrlr.Enabled[Tariff] = true and MaxElements[Tariff] > 0
    cp.variables = tariff_cost_ctrlr_variables()
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    try:
        # Configuration State: CSMS is configured to provide a driver specific tariff for
        # <Configured valid idToken> with
        #     - currency: <not omitted>
        #     - energy price: 0.25 per kWh (ex VAT), vat 20%
        #     - idle price: 0.10 per minute (ex VAT), vat 20%
        #     - fixed fee: 0.50 (ex VAT), vat 20%
        await set_driver_tariff(VALID_ID_TOKEN, VALID_ID_TOKEN_TYPE, {
            'tariffId': new_tariff_id(),
            'currency': 'EUR',
            'energy': {'prices': [{'priceKwh': 0.25}], 'taxRates': [VAT]},
            'idleTime': {'prices': [{'priceMinute': 0.10}], 'taxRates': [VAT]},
            'fixedFee': {'prices': [{'priceFixed': 0.50}], 'taxRates': [VAT]},
        })

        # 1. The Test System sends an AuthorizeRequest with
        #    - idToken.idToken <Configured valid_idtoken_idtoken>
        # 2. The CSMS responds with AuthorizeResponse
        response = await cp.call(call.Authorize(
            id_token={'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE}))
        validate_id_token_info('AuthorizeResponse', response.id_token_info, status='Accepted')
        tariff = response.tariff
        assert tariff is not None, "AuthorizeResponse has no tariff"
        assert tariff.tariff_id, "AuthorizeResponse.tariff.tariffId must not be omitted"
        assert tariff.currency, "AuthorizeResponse.tariff.currency must not be omitted"
        validate_price(tariff, 'energy', 'price_kwh', 0.25)
        validate_price(tariff, 'idle_time', 'price_minute', 0.10)
        validate_price(tariff, 'fixed_fee', 'price_fixed', 0.50)
    finally:
        # The other test cases are for an idToken without a driver-specific tariff.
        await set_driver_tariff(VALID_ID_TOKEN, VALID_ID_TOKEN_TYPE, None)

    start_task.cancel()
