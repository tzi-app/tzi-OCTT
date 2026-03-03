import json
import os
import ssl
import jsonschema
import base64
from pathlib import Path
from dataclasses import asdict
import humps
import logging
from datetime import datetime
import uuid
logging.basicConfig(level=logging.INFO)

_UTILS_DIR = Path(__file__).resolve().parent
_SCHEMA_DIR = _UTILS_DIR / 'schema'
_PROJECT_SCHEMA_DIR = _UTILS_DIR.parent / 'schema'
_VERSIONED_SCHEMA_DIRS = (
    _UTILS_DIR / '2.0.1' / 'schema',
    _UTILS_DIR / '2.1' / 'schema',
    _UTILS_DIR / '1.6' / 'schema',
)


def _resolve_path(path_value):
    path = Path(path_value)
    if path.is_absolute():
        return str(path)

    candidates = (
        Path.cwd() / path,
        _UTILS_DIR / path,
        _UTILS_DIR.parent / path,
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())
    return str((_UTILS_DIR / path).resolve())

def get_basic_auth_headers(username, password):
    auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}"
    }

    return headers


def validate_schema(data, schema_file_name):
    schema_candidates = [
        _SCHEMA_DIR / schema_file_name,
        _PROJECT_SCHEMA_DIR / schema_file_name,
    ]
    schema_candidates.extend(directory / schema_file_name for directory in _VERSIONED_SCHEMA_DIRS)

    schema_path = None
    for candidate in schema_candidates:
        if candidate.exists():
            schema_path = candidate
            break
    if schema_path is None:
        # Keep the same exception type, but surface all attempted roots.
        attempted = ', '.join(str(path.parent) for path in schema_candidates)
        raise FileNotFoundError(
            f"Schema '{schema_file_name}' not found. Tried: {attempted}"
        )

    schema_file_name = str(schema_path)
    with open(schema_file_name) as schema_file:
        schema = json.load(schema_file)
        data = humps.camelize(asdict(data))
        data = _remove_nones(data)
        try:
            is_valid, errors = validate_json_draft06(instance=data, schema=schema)
            if not is_valid:
                logging.info(errors)

            return is_valid
        except jsonschema.exceptions.ValidationError as err:
            logging.info(err.message)
            return False


def validate_json_draft06(instance, schema):
    validator = jsonschema.Draft6Validator(schema)

    errors = []
    for error in sorted(validator.iter_errors(instance), key=str):
        # Format error message with path
        path = ' -> '.join(str(p) for p in error.path) if error.path else 'root'
        errors.append(f"{path}: {error.message}")

    return len(errors) == 0, errors


def _remove_nones(data, depth=0):
    if depth > 5:
        return data

    if isinstance(data, dict):
        return {
            k: _remove_nones(v, depth + 1)
            for k, v in data.items()
            if v is not None and _remove_nones(v, depth + 1) is not None
        }
    elif isinstance(data, (list, tuple)):
        cleaned = [_remove_nones(x, depth + 1) for x in data if x is not None]
        return type(data)(cleaned)

    return data

def build_default_ssl_context():
    """Build an SSL context for wss:// connections using TLS_CA_CERT env var.
    Falls back to no cert verification for local dev when TLS_CA_CERT is unset."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ca_cert = os.environ.get('TLS_CA_CERT')
    if ca_cert:
        ctx.load_verify_locations(_resolve_path(ca_cert))
    else:
        ctx.verify_mode = ssl.CERT_NONE
    ctx.check_hostname = False
    return ctx


def create_ssl_context(ca_cert=None, client_cert=None, client_key=None,
                       max_tls_version=None, check_hostname=True):
    """Create SSL context for TLS WebSocket connections."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if not check_hostname:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    if ca_cert:
        ctx.load_verify_locations(_resolve_path(ca_cert))
    if client_cert:
        cert_path = _resolve_path(client_cert)
        key_path = _resolve_path(client_key) if client_key else None
        ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    if max_tls_version:
        ctx.maximum_version = max_tls_version
    return ctx


def get_tls_info(ws):
    """Extract TLS version, cipher, and peer cert from a websocket."""
    ssl_obj = ws.transport.get_extra_info('ssl_object')
    if not ssl_obj:
        return None
    return {
        'tls_version': ssl_obj.version(),
        'cipher': ssl_obj.cipher(),
        'peer_cert': ssl_obj.getpeercert(),
        'peer_cert_der': ssl_obj.getpeercert(binary_form=True),
    }


def validate_cert_key_size(der_cert):
    """Validate certificate public key meets OCPP minimum size requirements.
    RSA/DSA: >= 2048 bits, ECC: >= 224 bits.
    """
    from cryptography.x509 import load_der_x509_certificate
    from cryptography.hazmat.primitives.asymmetric import rsa, dsa, ec

    cert = load_der_x509_certificate(der_cert)
    public_key = cert.public_key()
    key_size = public_key.key_size

    if isinstance(public_key, (rsa.RSAPublicKey, dsa.DSAPublicKey)):
        assert key_size >= 2048, \
            f"RSA/DSA key must be at least 2048 bits, got {key_size}"
    elif isinstance(public_key, ec.EllipticCurvePublicKey):
        assert key_size >= 224, \
            f"ECC key must be at least 224 bits, got {key_size}"

    return key_size


def validate_cert_x509_pem(der_cert):
    """Validate that the certificate is valid X.509 and can be encoded as PEM."""
    from cryptography.x509 import load_der_x509_certificate
    from cryptography.hazmat.primitives.serialization import Encoding

    cert = load_der_x509_certificate(der_cert)
    pem_bytes = cert.public_bytes(Encoding.PEM)
    pem_str = pem_bytes.decode('utf-8')
    assert pem_str.startswith('-----BEGIN CERTIFICATE-----'), \
        "Certificate is not in valid X.509 PEM format"
    assert '-----END CERTIFICATE-----' in pem_str, \
        "Certificate is not in valid X.509 PEM format"
    return pem_str


def generate_csr(common_name):
    """Generate a CSR and private key for certificate signing tests.
    Returns (csr_pem_str, private_key).
    """
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography import x509
    from cryptography.x509.oid import NameOID

    private_key = ec.generate_private_key(ec.SECP256R1())
    csr = x509.CertificateSigningRequestBuilder().subject_name(
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    ).sign(private_key, hashes.SHA256())
    csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()
    return csr_pem, private_key


def save_private_key_to_temp(private_key):
    """Save a private key to a temporary file, return the path."""
    import tempfile
    from cryptography.hazmat.primitives import serialization

    key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    f = tempfile.NamedTemporaryFile(mode='wb', suffix='.pem', delete=False)
    f.write(key_bytes)
    f.close()
    return f.name


def save_cert_chain_to_temp(cert_chain_pem):
    """Save a PEM certificate chain string to a temporary file, return the path."""
    import tempfile

    f = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
    f.write(cert_chain_pem)
    f.close()
    return f.name


def now_iso():
    return datetime.now().isoformat() + "Z"

def generate_transaction_id():
    return str(uuid.uuid4())
