"""TLS and security profile helpers for the OCPP 2.1 block A tests."""

import asyncio
import contextlib
import logging
import os
import ssl
from urllib.parse import urlparse

import pytest

from charge_point import connect_to_csms
from contract_pki import CERTS_DIR, ROOT_CA, SUB_CA
from utils import (
    _resolve_path,
    create_ssl_context,
    generate_csr,
    get_basic_auth_headers,
    save_cert_chain_to_temp,
    save_private_key_to_temp,
    validate_cert_key_size,
    validate_cert_x509_pem,
)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
TLS_CA_CERT = os.environ['TLS_CA_CERT']
TLS_CLIENT_CERT = os.environ['TLS_CLIENT_CERT']
TLS_CLIENT_KEY = os.environ['TLS_CLIENT_KEY']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

# The configured V2G certificate chain of the Test System (contract_pki.py)
V2G_ROOT_CERT = CERTS_DIR / f'{ROOT_CA}.pem'
V2G_SUB_CA_CERT = CERTS_DIR / f'{SUB_CA}.pem'

ACCEPTABLE_TLS_VERSIONS = {'TLSv1.2', 'TLSv1.3'}

# The cipher suites a CSMS has to support at least (A00.FR.318), by their OpenSSL names:
# TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256, TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
# TLS_RSA_WITH_AES_128_GCM_SHA256, TLS_RSA_WITH_AES_256_GCM_SHA384
REQUIRED_TLS12_CIPHERS = (
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'AES128-GCM-SHA256',
    'AES256-GCM-SHA384',
)


def csms_host():
    """The FQDN of the CSMS endpoint."""
    return urlparse(CSMS_ADDRESS).hostname


def ssl_context_for(security_profile, client_cert=None, client_key=None):
    """The station's SSL context for a security profile. The client certificate is only sent
    with security profile 3."""
    if security_profile == 3:
        return create_ssl_context(
            ca_cert=TLS_CA_CERT,
            client_cert=client_cert or TLS_CLIENT_CERT,
            client_key=client_key or TLS_CLIENT_KEY,
        )
    return create_ssl_context(ca_cert=TLS_CA_CERT)


def headers_for(station_id, security_profile, password=None):
    """The HTTP upgrade request only has a username/password combination with security
    profile 1 or 2."""
    if security_profile == 3:
        return {}
    return get_basic_auth_headers(station_id, password or BASIC_AUTH_CP_PASSWORD)


async def connect_with_profile(station_id, security_profile, client_cert=None, client_key=None,
                               password=None):
    """Connect to the CSMS the way a station with this security profile does:
    1 and 2: TLS with Basic Auth (this suite runs security profile 1 over TLS as well);
    3: TLS with a client side certificate, and no Basic Auth.
    """
    return await connect_to_csms(
        station_id,
        headers=headers_for(station_id, security_profile, password),
        ssl_context=ssl_context_for(security_profile, client_cert, client_key),
    )


async def wait_for_basic_auth_password(cp, manual_action):
    """The setVariableData element with which the CSMS sets a new BasicAuthPassword (A01).

    A CSMS may send SetVariablesRequests of its own as well, for other variables. Those are
    answered and skipped.
    """
    request = await cp.wait_for_request('SetVariables', manual_action=manual_action)
    while True:
        for item in request.set_variable_data:
            if item.variable.name == 'BasicAuthPassword':
                return item
        logging.info(f"Ignoring non-BasicAuthPassword SetVariablesRequest: {request}")
        request = await cp.wait_for_request('SetVariables')


@contextlib.contextmanager
def client_certificate_files(certificate_chain, private_key):
    """The station's renewed certificate and its key as files, for an SSL context. Yields
    (certificate path, key path); the files are removed afterwards."""
    cert_path = save_cert_chain_to_temp(certificate_chain)
    key_path = save_private_key_to_temp(private_key)
    try:
        yield cert_path, key_path
    finally:
        os.unlink(cert_path)
        os.unlink(key_path)


def station_csr(common_name):
    """A CSR as the station generates it: for a new key pair, based on the configured Country,
    Organization and OrganizationalUnit. Returns (csr in PEM, private key)."""
    return generate_csr(
        common_name,
        country=os.environ['CONFIGURED_CSR_COUNTRY'],
        organization=os.environ['CONFIGURED_CSR_ORGANIZATION'],
        organizational_unit=os.environ['CONFIGURED_CSR_ORGANIZATIONAL_UNIT'],
    )


def _load_certificate(path):
    from cryptography import x509

    with open(_resolve_path(str(path)), 'rb') as certificate_file:
        return x509.load_pem_x509_certificate(certificate_file.read())


def validate_signed_certificate(certificate_chain, private_key, root_certificate_path,
                                sub_ca_certificate_paths=()):
    """Check the certificateChain of a CertificateSignedRequest: its first certificate is
    generated from the station's CSR, i.e. it is for the key of that CSR, and it is signed by
    the configured root certificate. That is directly, or through sub-CA certificates: the
    ones that follow it in the chain, and the configured ones. Returns the certificates of
    the chain.
    """
    from cryptography import x509

    try:
        certificates = x509.load_pem_x509_certificates(certificate_chain.encode())
    except ValueError as error:
        pytest.fail(f"certificateChain is not a chain of PEM encoded X.509 certificates: {error}")
    root = _load_certificate(root_certificate_path)

    certificate = certificates[0]
    assert certificate.public_key().public_numbers() == private_key.public_key().public_numbers(), \
        "The certificate is not generated from the CSR of the SignCertificateRequest: " \
        "its public key is not the key of the CSR"

    # Walk up from the certificate to the configured root.
    issuers = (certificates[1:] + [_load_certificate(path) for path in sub_ca_certificate_paths]
               + [root])
    for _ in range(len(issuers)):
        for issuer in issuers:
            try:
                certificate.verify_directly_issued_by(issuer)
            except Exception:
                continue
            if issuer == root:
                return certificates
            certificate = issuer
            break
        else:
            break
    pytest.fail(
        f"The certificate chain is not signed by the configured root certificate "
        f"({root.subject.rfc4514_string()}); the certificate "
        f"{certificate.subject.rfc4514_string()} is issued by {certificate.issuer.rfc4514_string()}")


def report_certificate_properties(certificates):
    """The checks on a signed certificate that do not fail a test case, "because generating
    the certificate is probably not done by the CSMS": the key must be at least 224 bits long,
    and the certificate must be X.509 in PEM. A violation is reported as a warning.
    """
    from cryptography.hazmat.primitives.serialization import Encoding

    for certificate in certificates:
        try:
            validate_cert_key_size(certificate.public_bytes(Encoding.DER))
            validate_cert_x509_pem(certificate.public_bytes(Encoding.DER))
        except AssertionError as violation:
            logging.warning(f"Certificate {certificate.subject.rfc4514_string()}: {violation}")


def validate_server_certificate(peer_cert, peer_cert_der, server_host):
    """The checks on a certificate the CSMS served in a TLS handshake.

    A00.FR.508 (serial number), A00.FR.510 (the CN is the FQDN of the endpoint), A00.FR.502
    and A00.FR.503 (key size), A00.FR.507 (X.509, PEM). Returns (commonName, serialNumber,
    key size).
    """
    assert peer_cert, "Peer certificate must be present"

    subject = dict(x[0] for x in peer_cert.get('subject', ()))
    assert 'commonName' in subject, "Certificate subject must contain commonName"
    assert peer_cert.get('serialNumber'), "Certificate must include a serial number"
    assert subject.get('commonName') == server_host, \
        f"Certificate commonName must match endpoint FQDN ({server_host}), got {subject.get('commonName')}"

    # Public key size: RSA/DSA >= 2048, ECC >= 224
    key_size = validate_cert_key_size(peer_cert_der)

    validate_cert_x509_pem(peer_cert_der)

    return subject.get('commonName'), peer_cert.get('serialNumber'), key_size


async def assert_tls12_ciphers_supported(security_profile, validate_certificate=False):
    """A00.FR.318: the CSMS completes a TLS 1.2 handshake with each required cipher suite.

    Each suite gets a TLS handshake of its own, which is closed without an HTTP upgrade. That
    makes it a check of the TLS layer, and the CSMS does not see it as a connection of the
    station. A completed WebSocket connection with the station's identity would replace the
    connection the scenario continues on, because a station has one connection at a time.

    With validate_certificate, the certificate served for each suite is validated as well.
    The ECDHE_ECDSA suites are served the CSMS's EC certificate, and the TLS_RSA suites its
    RSA certificate (A00.FR.318 note).
    """
    endpoint = urlparse(CSMS_ADDRESS)
    host, port = endpoint.hostname, endpoint.port or 443
    for cipher in REQUIRED_TLS12_CIPHERS:
        ssl_ctx = ssl_context_for(security_profile)
        ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ssl_ctx.set_ciphers(cipher)

        try:
            _, writer = await asyncio.open_connection(host, port, ssl=ssl_ctx, server_hostname=host)
        except Exception as exc:
            pytest.fail(f"Required TLS 1.2 cipher not supported: {cipher}, error={exc}")

        try:
            ssl_obj = writer.get_extra_info('ssl_object')
            negotiated = ssl_obj.cipher()[0]
            assert negotiated == cipher, f"Expected TLS 1.2 cipher {cipher}, negotiated {negotiated}"

            if validate_certificate:
                common_name, serial, key_size = validate_server_certificate(
                    ssl_obj.getpeercert(), ssl_obj.getpeercert(binary_form=True), host)
                logging.info(f"TLS 1.2: cipher={negotiated}, key_size={key_size}, "
                             f"CN={common_name}, serial={serial}")
        finally:
            writer.close()
            with contextlib.suppress(ConnectionError, ssl.SSLError):
                await writer.wait_closed()
