"""Helpers for the ad hoc payment tests of OCPP 2.1 (use cases C18 - C25)."""

import hashlib
import hmac
import os
import time
import uuid

_BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

# The WebPaymentsCtrlr values of the QR code test cases (TC_C_131 - TC_C_133)
QR_CODE_VALIDITY_TIME = 30
QR_CODE_TOTP_LENGTH = 8
QR_CODE_TOTP_VERSION = '1'


def totp_v1(shared_secret, validity_time=QR_CODE_VALIDITY_TIME, length=QR_CODE_TOTP_LENGTH,
            at=None):
    """The time-based one-time password of a dynamic QR code: "TOTP algorithm, version 1" of
    use case C25. `at` is the time in seconds since the Unix epoch; by default the current
    time."""
    time_interval = int((time.time() if at is None else at) // validity_time)
    digest = hmac.new(shared_secret.encode('utf-8'), time_interval.to_bytes(8, 'big'),
                      hashlib.sha256).digest()
    offset = digest[-1] & 0x0F
    return ''.join(_BASE62[digest[(offset + i) % len(digest)] % len(_BASE62)]
                   for i in range(length))


def qr_code_url(charging_station_id, evse_id, totp, max_energy=None):
    """The URL of a dynamic QR code, as the station fills in WebPaymentsCtrlr.URLTemplate:
    <base-url>/{chargingstationid}/{evse}/{totp}/{version}, with the query parameter maxenergy
    (in Wh) when the EV Driver specified a maximum energy to charge (C25.FR.05).

    charging_station_id None leaves that path parameter out, for an invalid URL.
    """
    parts = [os.environ['QR_CODE_BASE_URL'].rstrip('/')]
    if charging_station_id is not None:
        parts.append(charging_station_id)
    parts += [str(evse_id), totp, QR_CODE_TOTP_VERSION]
    url = '/'.join(parts)
    if max_energy is not None:
        url += f"?maxenergy={max_energy}"
    return url


def web_payments_ctrlr_variables():
    """The WebPaymentsCtrlr variables the Test System has in the QR code test cases, for the
    station's answer to a GetVariablesRequest (TziChargePoint21.variables). SharedSecret is
    write-only, so it is not among them."""
    return {
        'WebPaymentsCtrlr.Enabled': 'true',
        'WebPaymentsCtrlr.URLTemplate':
            os.environ['QR_CODE_BASE_URL'].rstrip('/') + '/{chargingstationid}/{evse}/{totp}/{version}',
        'WebPaymentsCtrlr.ValidityTime': str(QR_CODE_VALIDITY_TIME),
        'WebPaymentsCtrlr.Length': str(QR_CODE_TOTP_LENGTH),
        'WebPaymentsCtrlr.TOTPVersion': QR_CODE_TOTP_VERSION,
    }


def new_psp_ref():
    """A reference of an ad hoc payment at the payment service provider (PSP)."""
    return f"PSP-{uuid.uuid4()}"


def direct_payment_id_token(psp_ref, payment_details_type='CardLast4Digits', payment_details='1234'):
    """The idToken of an ad hoc payment (C18.FR.06): the PspRef with type DirectPayment, and the
    payment details that PaymentCtrlr.PaymentDetails configures in additionalInfo."""
    return {
        'id_token': psp_ref,
        'type': 'DirectPayment',
        'additional_info': [{'additional_id_token': payment_details, 'type': payment_details_type}],
    }


def payment_ctrlr_variables(authorize_direct_payment=False, authorization_amount='50.00',
                            payment_details='CardLast4Digits', settlement_by_csms=False,
                            receipt_by_csms=None):
    """The PaymentCtrlr variables the Test System has in a test case, for the station's answer
    to a GetVariablesRequest (TziChargePoint21.variables)."""
    variables = {
        'PaymentCtrlr.Enabled': 'true',
        'PaymentCtrlr.AuthorizeDirectPayment': 'true' if authorize_direct_payment else 'false',
        'PaymentCtrlr.AuthorizationAmount': authorization_amount,
        'PaymentCtrlr.PaymentDetails': payment_details,
        'PaymentCtrlr.SettlementByCSMS': 'true' if settlement_by_csms else 'false',
    }
    if receipt_by_csms is not None:
        variables['PaymentCtrlr.ReceiptByCSMS'] = 'true' if receipt_by_csms else 'false'
    return variables


def fixed_fee_cost_details():
    """The costDetails of the settlement test cases: a fixed fee of 15.00 EUR excluding and
    18.15 EUR including 21 % "MyTax", for 123 Wh in 5 seconds of charging. chargingPeriods is
    omitted."""
    return {
        'total_cost': {
            'currency': 'EUR',
            'type_of_cost': 'NormalCost',
            'fixed': {
                'excl_tax': 15.00,
                'incl_tax': 18.15,
                'tax_rates': [{'type': 'MyTax', 'tax': 21}],
            },
            'total': {'excl_tax': 15.00, 'incl_tax': 18.15},
        },
        'total_usage': {'energy': 123, 'charging_time': 5, 'idle_time': 0},
    }
