"""The energy meter of the mock Charging Station (OCPP 2.1, block J): readings of the energy
register, clock-aligned and periodic sampling, and signed meter values."""

import asyncio
import base64
import json
import math
import time
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

# A SigningMethodEnumStringType of the OCPP 2.1 appendices
SIGNING_METHOD = 'ECDSA-secp256r1-SHA256'
# SignedMeterValueType.encodingMethod: "Format used by the energy meter to encode the meter data"
ENCODING_METHOD = 'OCMF'

_METER_SERIAL_NUMBER = 'TZI-METER-0001'

# OCMF "TX": the type of a reading, for the reading contexts of a transaction
_OCMF_READING_TYPE = {'Transaction.Begin': 'B', 'Transaction.End': 'E'}

_meter_key = None


def _key():
    """The private key of the meter. The meter gets it the first time it has to sign."""
    global _meter_key
    if _meter_key is None:
        _meter_key = ec.generate_private_key(ec.SECP256R1())
    return _meter_key


def meter_public_key():
    """The public key of the meter: the Base64 encoded SubjectPublicKeyInfo (DER)."""
    der = _key().public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return base64.b64encode(der).decode('ascii')


def signed_meter_value(value, timestamp, context='Sample.Periodic', unit='Wh', public_key=True):
    """A generated SignedMeterValueType for the reading `value` of the energy register.

    signedMeterData is the reading in the OCMF format ("OCMF|<data>|<signature>"), signed by
    the meter and Base64 encoded. public_key=False leaves the publicKey out, as a station does
    when PublicKeyWithSignedMeterValue says it was sent already.
    """
    data = json.dumps({
        'FV': '1.0',
        'GI': 'TZI mock energy meter',
        'GS': _METER_SERIAL_NUMBER,
        'PG': 'T1',
        'MS': _METER_SERIAL_NUMBER,
        'RD': [{
            'TM': timestamp,
            'TX': _OCMF_READING_TYPE.get(context, 'P'),
            'RV': value,
            'RI': '1-b:1.8.0',
            'RU': unit,
            'ST': 'G',
        }],
    }, separators=(',', ':'))
    signature = _key().sign(data.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
    ocmf = f"OCMF|{data}|" + json.dumps({'SA': SIGNING_METHOD, 'SD': signature.hex()},
                                         separators=(',', ':'))
    signed = {
        'signed_meter_data': base64.b64encode(ocmf.encode('utf-8')).decode('ascii'),
        'signing_method': SIGNING_METHOD,
        'encoding_method': ENCODING_METHOD,
    }
    if public_key:
        signed['public_key'] = meter_public_key()
    return signed


# ─── Meter values ────────────────────────────────────────────────────────────

def utc_iso(epoch_seconds):
    """The dateTime of a moment given in seconds since the Unix epoch, as utc_now_iso()."""
    moment = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    return moment.isoformat(timespec='milliseconds').replace('+00:00', 'Z')


async def ticks(interval, clock_aligned=False):
    """Wait for the moments at which a station samples its meter, and yield each of them
    (seconds since the Unix epoch): every `interval` seconds from now, or with clock_aligned
    at the whole multiples of the interval, as for the clock-aligned meter values of J01."""
    if clock_aligned:
        moment = (math.floor(time.time() / interval) + 1) * interval
    else:
        moment = time.time() + interval
    while True:
        await asyncio.sleep(max(0.0, moment - time.time()))
        yield moment
        moment += interval


class EnergyMeter:
    """The energy meter of an EVSE of the mock Charging Station. Its register (Wh) goes up
    with the power (W) that flows through it."""

    def __init__(self, power=0.0, register=0.0):
        self._power = power
        self._register = register
        self._since = time.time()
        self._public_key_sent = False

    def reading(self, at=None):
        """The value of the register now, or at a moment (seconds since the Unix epoch)."""
        elapsed = (time.time() if at is None else at) - self._since
        return round(self._register + self._power * max(0.0, elapsed) / 3600, 1)

    def meter_value(self, context, at=None, signed=False):
        """A MeterValueType with one reading of the register, taken now or at a moment.

        signed: the sampledValue has a signedMeterValue. The public key of the meter goes
        with the first one (PublicKeyWithSignedMeterValue OncePerTransaction).
        """
        at = time.time() if at is None else at
        timestamp = utc_iso(at)
        sampled_value = {'value': self.reading(at), 'context': context}
        if signed:
            sampled_value['signed_meter_value'] = signed_meter_value(
                sampled_value['value'], timestamp, context=context,
                public_key=not self._public_key_sent)
            self._public_key_sent = True
        return {'timestamp': timestamp, 'sampled_value': [sampled_value]}


class MeterValueSampler:
    """Samples a meter in the background at every tick, as a Charging Station does during a
    transaction for the meter values of the TransactionEventRequest with eventType Ended
    (SampledDataCtrlr.TxEndedInterval and AlignedDataCtrlr.TxEndedInterval)."""

    def __init__(self, meter, interval, context, clock_aligned=False, signed=False):
        self._meter = meter
        self._signed = signed
        self.meter_values = []
        self._task = asyncio.ensure_future(self._sample(interval, context, clock_aligned))

    async def _sample(self, interval, context, clock_aligned):
        async for moment in ticks(interval, clock_aligned):
            self.meter_values.append(
                self._meter.meter_value(context, at=moment, signed=self._signed))

    def stop(self, end_context='Transaction.End'):
        """Stop sampling. Returns the sampled meter values, followed by a last reading with
        the context of the end of the transaction."""
        self._task.cancel()
        return self.meter_values + [self._meter.meter_value(end_context, signed=self._signed)]
