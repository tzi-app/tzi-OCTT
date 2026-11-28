"""The certificates of the certificate management tests of OCPP 2.1 (block M): the configured
certificate of each certificateType, and the hash data that a Charging Station reports for
them."""

import datetime
from functools import lru_cache
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509 import ocsp
from cryptography.x509.oid import NameOID

_CERTS_DIR = Path(__file__).resolve().parent.parent / 'certs'

HASH_ALGORITHMS = {'SHA256': hashes.SHA256, 'SHA384': hashes.SHA384, 'SHA512': hashes.SHA512}

# The root certificates of the Test System that come from its certificate files
_ROOT_CERTIFICATE_FILES = {
    'CSMSRootCertificate': 'ca.pem',
    'V2GRootCertificate': 'v2g_root_ca.pem',
}
# The other root certificates are made for the test run.
_GENERATED_ROOT_CERTIFICATES = {
    'MORootCertificate': 'TZI OCTT MO Root CA',
    'ManufacturerRootCertificate': 'TZI OCTT Manufacturer Root CA',
    'OEMRootCertificate': 'TZI OCTT OEM Root CA',
}
ROOT_CERTIFICATE_TYPES = tuple(_ROOT_CERTIFICATE_FILES) + tuple(_GENERATED_ROOT_CERTIFICATES)

# The V2G certificate chain of the Test System: the certificate of the station and its sub-CA
_V2G_CHAIN_FILES = ('contract_leaf.pem', 'contract_sub_ca.pem', 'v2g_root_ca.pem')


def _self_signed_root(common_name):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'TZI Test'),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    now = datetime.datetime.now(datetime.timezone.utc)
    return (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )


def _load(file_name):
    return x509.load_pem_x509_certificate((_CERTS_DIR / file_name).read_bytes())


@lru_cache(maxsize=None)
def _root(certificate_type):
    if certificate_type in _ROOT_CERTIFICATE_FILES:
        return _load(_ROOT_CERTIFICATE_FILES[certificate_type])
    return _self_signed_root(_GENERATED_ROOT_CERTIFICATES[certificate_type])


def configured_certificate(certificate_type):
    """<The configured certificate of the specified certificateType>, PEM encoded."""
    return _root(certificate_type).public_bytes(serialization.Encoding.PEM).decode('ascii')


def _hash_data(certificate, issuer, hash_algorithm):
    """The CertificateHashDataType of a certificate (snake_case): the hashes of the name and
    the public key of its issuer, and its serial number, hex encoded."""
    request = ocsp.OCSPRequestBuilder().add_certificate(
        certificate, issuer, HASH_ALGORITHMS[hash_algorithm]()).build()
    return {
        'hash_algorithm': hash_algorithm,
        'issuer_name_hash': request.issuer_name_hash.hex(),
        'issuer_key_hash': request.issuer_key_hash.hex(),
        'serial_number': format(certificate.serial_number, 'X'),
    }


def certificate_hash_data_chain(certificate_type, hash_algorithm='SHA256'):
    """The CertificateHashDataChainType that the Test System reports for the installed
    certificate of a certificateType (snake_case).

    For V2GCertificateChain it is the hash data of the V2G certificate of the Charging Station,
    with its sub-CA certificate as child (M03.FR.05).
    """
    if certificate_type == 'V2GCertificateChain':
        leaf, sub_ca, root = (_load(file_name) for file_name in _V2G_CHAIN_FILES)
        return {
            'certificate_type': certificate_type,
            'certificate_hash_data': _hash_data(leaf, sub_ca, hash_algorithm),
            'child_certificate_hash_data': [_hash_data(sub_ca, root, hash_algorithm)],
        }
    root = _root(certificate_type)
    return {
        'certificate_type': certificate_type,
        'certificate_hash_data': _hash_data(root, root, hash_algorithm),
    }


def trust_store(hash_algorithm='SHA256'):
    """The hash data of all certificates that are stored at the Test System."""
    return [certificate_hash_data_chain(certificate_type, hash_algorithm)
            for certificate_type in ROOT_CERTIFICATE_TYPES + ('V2GCertificateChain',)]


def is_certificate(pem):
    """Whether a string is a PEM encoded X.509 certificate."""
    try:
        x509.load_pem_x509_certificate(pem.encode('ascii'))
    except (ValueError, UnicodeEncodeError):
        return False
    return True
