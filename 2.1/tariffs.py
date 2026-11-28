"""Tariffs for the local cost calculation tests of OCPP 2.1 (use cases I07 - I12).

The tariffs are given as they go on the wire (the field names of the OCPP 2.1 schemas): they
are the payloads of the trigger API calls that make the CSMS send a tariff.
"""

import re
import uuid

from ocpp_messages import utc_now_iso

# RFC 3339: time-hour ":" time-minute
_TIME_OF_DAY = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')

CURRENCY = 'EUR'
VAT = {'type': 'VAT', 'tax': 20}


def new_tariff_id():
    return f"tariff-{uuid.uuid4().hex[:12]}"


def tariff_cost_ctrlr_variables(conditions_supported=True, max_elements=10, **more):
    """The TariffCostCtrlr variables of a Test System that supports local cost calculation,
    for the station's answer to a GetVariablesRequest (TziChargePoint21.variables).

    more: other variables by instance name, for example Cost='true', RunningCost='true'
    for TariffCostCtrlr.Enabled[Cost] and TariffCostCtrlr.Enabled[RunningCost].
    """
    variables = {
        'TariffCostCtrlr.Enabled[Tariff]': 'true',
        'TariffCostCtrlr.MaxElements[Tariff]': str(max_elements),
        'TariffCostCtrlr.ConditionsSupported[Tariff]': 'true' if conditions_supported else 'false',
        'TariffCostCtrlr.Currency': CURRENCY,
    }
    for instance, value in more.items():
        variables[f'TariffCostCtrlr.Enabled[{instance}]'] = value
    return variables


def energy_tariff(price_kwh=0.30):
    """A tariff with one price for energy."""
    return {
        'tariffId': new_tariff_id(),
        'currency': CURRENCY,
        'energy': {'prices': [{'priceKwh': price_kwh}]},
    }


def time_of_day_tariff(prices):
    """A tariff with validFrom and prices for energy with a condition on startTimeOfDay and
    endTimeOfDay. prices: (startTimeOfDay, endTimeOfDay, priceKwh) per price."""
    return {
        'tariffId': new_tariff_id(),
        'currency': CURRENCY,
        'validFrom': utc_now_iso(),
        'energy': {'prices': [
            {'priceKwh': price_kwh, 'conditions': {'startTimeOfDay': start, 'endTimeOfDay': end}}
            for start, end, price_kwh in prices
        ]},
    }


# Price for energy in peak hours, price for energy other hours
PEAK_AND_OTHER_HOURS = [('08:00', '20:00', 0.45), ('20:00', '08:00', 0.25)]


def validate_time_of_day_prices(message, tariff, number_of_prices=1):
    """The tool validations of a tariff with time-of-day prices for energy: validFrom, and per
    price the priceKwh and a startTimeOfDay and endTimeOfDay in the format of RFC 3339
    (time-hour ":" time-minute)."""
    assert tariff.valid_from is not None, f"{message}.tariff.validFrom must not be omitted"
    assert tariff.energy is not None, f"{message}.tariff has no energy"
    prices = tariff.energy.prices
    assert len(prices) >= number_of_prices, \
        f"Expected {number_of_prices} prices in {message}.tariff.energy.prices, got {len(prices)}"
    for index in range(number_of_prices):
        where = f"{message}.tariff.energy.prices[{index}]"
        price = prices[index]
        assert price.price_kwh is not None, f"{where}.priceKwh must not be omitted"
        assert price.conditions is not None, f"{where} has no conditions"
        for field, value in (('startTimeOfDay', price.conditions.start_time_of_day),
                             ('endTimeOfDay', price.conditions.end_time_of_day)):
            assert value is not None and _TIME_OF_DAY.match(value), \
                f"{where}.conditions.{field} must be in the format time-hour \":\" time-minute " \
                f"of RFC 3339, got {value!r}"


def full_tariff(reservation=None, valid_from=True, fixed_fee=0.50, tax_rate=None):
    """A tariff with a price for energy, chargingTime, idleTime and fixedFee, and a minCost
    and maxCost, each with a taxRate.

    reservation: 'reservationTime' or 'reservationFixed' adds that price with a taxRate.
    """
    tax_rates = [dict(tax_rate or VAT)]
    tariff = {
        'tariffId': new_tariff_id(),
        'currency': CURRENCY,
        'energy': {'prices': [{'priceKwh': 0.25}], 'taxRates': tax_rates},
        'chargingTime': {'prices': [{'priceMinute': 0.05}], 'taxRates': tax_rates},
        'idleTime': {'prices': [{'priceMinute': 0.10}], 'taxRates': tax_rates},
        'fixedFee': {'prices': [{'priceFixed': fixed_fee}], 'taxRates': tax_rates},
        'minCost': _price(2.00, tax_rates),
        'maxCost': _price(50.00, tax_rates),
    }
    if valid_from:
        tariff['validFrom'] = utc_now_iso()
    if reservation == 'reservationTime':
        tariff['reservationTime'] = {'prices': [{'priceMinute': 0.02}], 'taxRates': tax_rates}
    elif reservation == 'reservationFixed':
        tariff['reservationFixed'] = {'prices': [{'priceFixed': 1.00}], 'taxRates': tax_rates}
    return tariff


def _price(excl_tax, tax_rates):
    incl_tax = excl_tax
    for tax_rate in tax_rates:
        incl_tax += excl_tax * tax_rate['tax'] / 100
    return {'exclTax': excl_tax, 'inclTax': round(incl_tax, 2), 'taxRates': tax_rates}


def validate_full_tariff(message, tariff, reservation=None, valid_from=True,
                         excl_and_incl_tax=True):
    """The tool validations of a tariff as full_tariff() makes it: every element is there,
    with its taxRates.

    excl_and_incl_tax: minCost and maxCost must have both exclTax and inclTax; False: at
    least one of the two.
    """
    assert tariff.tariff_id, f"{message}.tariff.tariffId must not be omitted"
    if valid_from:
        assert tariff.valid_from is not None, f"{message}.tariff.validFrom must not be omitted"
    elements = [('energy', tariff.energy), ('chargingTime', tariff.charging_time),
                ('idleTime', tariff.idle_time), ('fixedFee', tariff.fixed_fee),
                ('minCost', tariff.min_cost), ('maxCost', tariff.max_cost)]
    if reservation == 'reservationTime':
        elements.append(('reservationTime', tariff.reservation_time))
    elif reservation == 'reservationFixed':
        elements.append(('reservationFixed', tariff.reservation_fixed))
    for name, element in elements:
        assert element is not None, f"{message}.tariff.{name} must not be omitted"
        assert element.tax_rates, f"{message}.tariff.{name}.taxRates must not be omitted"
    for name, price in (('minCost', tariff.min_cost), ('maxCost', tariff.max_cost)):
        if excl_and_incl_tax:
            assert price.excl_tax is not None, f"{message}.tariff.{name}.exclTax must not be omitted"
            assert price.incl_tax is not None, f"{message}.tariff.{name}.inclTax must not be omitted"
        else:
            assert price.excl_tax is not None or price.incl_tax is not None, \
                f"{message}.tariff.{name} must have exclTax or inclTax"
