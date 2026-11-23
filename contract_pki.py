"""
The configured (V2G) certificate chain of the Test System, for the ISO 15118 contract certificate
tests (TC_C_50, TC_C_51, TC_C_52) and the Charging Station certificate status test (TC_M_24).

    certs/v2g_root_ca.pem      Root CA. The CSMS is configured to trust it; in tzi-csms:
                               CONTRACT_CERTIFICATE_TRUSTED_CA_PEM_PATH=../tzi-OCTT/certs/v2g_root_ca.pem
    certs/contract_sub_ca.pem  Sub-CA, issued by the root.
    certs/contract_leaf.pem    Contract certificate, issued by the sub-CA. CN = the configured eMAID.

generate_contract_certs.sh makes the certificates and their keys. mock_ocsp_responder.py answers
for the root and the sub-CA with these keys.
"""

from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509 import ocsp
from cryptography.x509.oid import AuthorityInformationAccessOID, ExtensionOID
from ocpp.v201.datatypes import OCSPRequestDataType
from ocpp.v201.enums import HashAlgorithmEnumType

CERTS_DIR = Path(__file__).resolve().parent / 'certs'

ROOT_CA = 'v2g_root_ca'
SUB_CA = 'contract_sub_ca'
CONTRACT = 'contract_leaf'


def load_certificate(name):
    return x509.load_pem_x509_certificate((CERTS_DIR / f'{name}.pem').read_bytes())


def load_private_key(name):
    return serialization.load_pem_private_key((CERTS_DIR / f'{name}.key').read_bytes(), password=None)


def contract_chain_with_issuers():
    """(certificate, issuer) for each certificate of the chain below the root: the contract
    certificate and the sub-CA."""
    root, sub_ca, contract = (load_certificate(name) for name in (ROOT_CA, SUB_CA, CONTRACT))
    return [(contract, sub_ca), (sub_ca, root)]


def ocsp_request_data(certificate, issuer, responder_url):
    """OCSPRequestDataType about `certificate` as a Charging Station sends it: the SHA-256 hashes of
    the issuer's name and public key, and the serial number, hex encoded, with the responder URL."""
    request = ocsp.OCSPRequestBuilder().add_certificate(certificate, issuer, hashes.SHA256()).build()
    return OCSPRequestDataType(
        hash_algorithm=HashAlgorithmEnumType.sha256,
        issuer_name_hash=request.issuer_name_hash.hex(),
        issuer_key_hash=request.issuer_key_hash.hex(),
        serial_number=format(certificate.serial_number, 'X'),
        responder_url=responder_url,
    )


def contract_chain_hash_data(responder_url):
    """iso15118CertificateHashData of the configured contract certificate chain (C07.FR.02): the
    contract certificate and its sub-CA, both with `responder_url`."""
    return [ocsp_request_data(certificate, issuer, responder_url)
            for certificate, issuer in contract_chain_with_issuers()]


def contract_chain_pem():
    """The contract certificate followed by its sub-CA, in PEM (C07.FR.06)."""
    return ''.join(load_certificate(name).public_bytes(serialization.Encoding.PEM).decode('ascii')
                   for name in (CONTRACT, SUB_CA))


def contract_ocsp_url():
    """The OCSP responder URL that the contract certificate names (Authority Information Access)."""
    access = load_certificate(CONTRACT).extensions.get_extension_for_oid(
        ExtensionOID.AUTHORITY_INFORMATION_ACCESS).value
    return next(description.access_location.value for description in access
                if description.access_method == AuthorityInformationAccessOID.OCSP)
