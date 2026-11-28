"""The firmware of the firmware management tests of OCPP 2.1 (block L): where it is, and the
Firmware Signing certificate and the signature that the CSMS has for it."""

import base64
import datetime
import hashlib
import os
from functools import lru_cache

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from trigger import send_call

# <Configured firmware_location>
FIRMWARE_LOCATION = os.environ['CONFIGURED_FIRMWARE_LOCATION']

# The firmware image of the test cases
_FIRMWARE_IMAGE = b'TZI OCTT firmware image 2.1.0\n' * 64

# How far in the future the retrieveDateTime or installDateTime of a scheduled firmware update
# is, in seconds
SCHEDULE_DELAY = 5


@lru_cache(maxsize=None)
def _signing_material():
    """The Firmware Signing certificate of the manufacturer (PEM) and the signature over the
    firmware image: RSA-PSS with SHA256 (L01.FR.04), Base64 encoded."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'TZI Test'),
        x509.NameAttribute(NameOID.COMMON_NAME, 'TZI OCTT Firmware Signing'),
    ])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.KeyUsage(
            digital_signature=True, content_commitment=False, key_encipherment=False,
            data_encipherment=False, key_agreement=False, key_cert_sign=False, crl_sign=False,
            encipher_only=False, decipher_only=False), critical=True)
        .sign(key, hashes.SHA256())
    )
    signature = key.sign(
        _FIRMWARE_IMAGE,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256())
    return (certificate.public_bytes(serialization.Encoding.PEM).decode('ascii'),
            base64.b64encode(signature).decode('ascii'))


def signing_certificate():
    """<Configured signingCertificate>: the PEM encoded Firmware Signing certificate."""
    return _signing_material()[0]


def signature():
    """<Configured signature>: the Base64 encoded signature of the firmware."""
    return _signing_material()[1]


def checksum():
    """The MD5 checksum over the entire firmware file, as PublishFirmwareRequest has it."""
    return hashlib.md5(_FIRMWARE_IMAGE).hexdigest()


def seconds_until(date_time):
    """The seconds from now until an OCPP dateTime; negative when it has passed."""
    moment = datetime.datetime.fromisoformat(date_time.upper().replace('Z', '+00:00'))
    return (moment - datetime.datetime.now(datetime.timezone.utc)).total_seconds()


async def request_firmware_update(cp: TziChargePoint21, status: str = 'Accepted',
                                  request_id: int = 1, retrieve_in: int = 0,
                                  install_in: int = None):
    """The Manual Action that makes the CSMS send an UpdateFirmwareRequest for the firmware of
    the test cases, which the Test System answers with `status`.

    retrieve_in, install_in: the seconds from now of retrieveDateTime and installDateTime.
    Returns the UpdateFirmwareRequest of the CSMS.
    """
    firmware = {
        'location': FIRMWARE_LOCATION,
        'retrieveDateTime': utc_now_iso(retrieve_in),
        'signingCertificate': signing_certificate(),
        'signature': signature(),
    }
    if install_in is not None:
        firmware['installDateTime'] = utc_now_iso(install_in)
    cp.set_response('UpdateFirmware', status=status)
    return await cp.wait_for_request(
        'UpdateFirmware',
        manual_action=send_call(cp.id, 'UpdateFirmware',
                                {'requestId': request_id, 'firmware': firmware}))


async def request_publish_firmware(cp: TziChargePoint21, status: str = 'Accepted',
                                   request_id: int = 1):
    """The Manual Action that makes the CSMS send a PublishFirmwareRequest for the firmware of
    the test cases, which the Test System answers with `status`. Returns the request, of which
    the location has been validated: location <Configured firmware_location>."""
    cp.set_response('PublishFirmware', status=status)
    request = await cp.wait_for_request(
        'PublishFirmware',
        manual_action=send_call(cp.id, 'PublishFirmware', {
            'location': FIRMWARE_LOCATION,
            'checksum': checksum(),
            'requestId': request_id,
        }))
    assert request.location == FIRMWARE_LOCATION, \
        f"Expected PublishFirmwareRequest.location {FIRMWARE_LOCATION}, got {request.location}"
    return request


async def reboot_with_new_firmware(cp: TziChargePoint21):
    """The Charging Station reboots to activate the firmware that it installed:

        The Test System sends a BootNotificationRequest With reason FirmwareUpdate
        The CSMS responds with a BootNotificationResponse    - status Accepted
        The Test System notifies the CSMS about the current state of all connectors.
            Message: StatusNotificationRequest - connectorStatus Available
            Message: NotifyEventRequest - trigger Delta, actualValue "Available",
                     component.name "Connector", variable.name "AvailabilityState"
        The CSMS responds accordingly.
    """
    boot_response = await cp.send_boot_notification(reason='FirmwareUpdate')
    assert boot_response.status == 'Accepted', \
        f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"
    await cp.send_all_connectors_status('Available')
