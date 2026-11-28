"""
Mock OCSP responder: the OCSP service of the Test System in TC_C_50, TC_C_51, TC_C_52 and TC_M_24.

It answers like the OCSP responder of a CA (IETF RFC 6960):
- It reads the CertID of the request: hash algorithm, issuer name hash, issuer key hash and serial
  number.
- It answers with a basic OCSP response about exactly that certificate: good, revoked or unknown.
  The answer is current (thisUpdate a few minutes ago, nextUpdate a day ahead) and carries the nonce
  of the request, if the request has one.
- The answer is signed by the CA that issued the certificate, which it names by its key hash. For a
  sub-CA the response carries the sub-CA certificate, so that the CSMS can follow it to the root.
- It refuses a request about a certificate of an issuer it does not know ("unauthorized"), and a
  request it cannot read ("malformedRequest").

By default it answers for the CAs of the configured (V2G) certificate chain (contract_pki.py):
certs/v2g_root_ca and certs/contract_sub_ca. A CSMS that verifies OCSP answers only takes them when
it trusts certs/v2g_root_ca.pem (tzi-csms: CONTRACT_CERTIFICATE_TRUSTED_CA_PEM_PATH).

Every request is recorded in `requests`, so that a test can check what the CSMS asked about.

Usage:
    responder = MockOCSPResponder(port=19080, cert_status="good")
    responder.start()
    ...
    responder.stop()
"""

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509 import ocsp

import contract_pki
from utils import LocalHTTPServer

_CERT_STATUSES = {
    'good': ocsp.OCSPCertStatus.GOOD,
    'revoked': ocsp.OCSPCertStatus.REVOKED,
    'unknown': ocsp.OCSPCertStatus.UNKNOWN,
}


def _issuer_hashes(issuer, algorithm):
    """(issuerNameHash, issuerKeyHash) of a CertID about a certificate that `issuer` issued
    (RFC 6960 section 4.1.1): the hashes of the issuer's distinguished name and of its public
    key, with `algorithm`."""
    name_hash = hashes.Hash(algorithm)
    name_hash.update(issuer.subject.public_bytes())
    # cryptography takes the key hash from the issuer passed in, and the name hash from the issuer
    # field of the certificate passed in, so only the key hash of this request is the issuer's.
    key_hash = ocsp.OCSPRequestBuilder().add_certificate(issuer, issuer, algorithm).build().issuer_key_hash
    return name_hash.finalize(), key_hash


def _unsuccessful(status):
    return ocsp.OCSPResponseBuilder.build_unsuccessful(status).public_bytes(serialization.Encoding.DER)


@dataclass
class ReceivedOCSPRequest:
    """The CertID of an OCSP request the responder received."""
    hash_algorithm: hashes.HashAlgorithm
    issuer_name_hash: bytes
    issuer_key_hash: bytes
    serial_number: int

    def is_about(self, certificate, issuer):
        """Whether the request asks about `certificate`, issued by `issuer`."""
        return (self.serial_number == certificate.serial_number
                and (self.issuer_name_hash, self.issuer_key_hash) == _issuer_hashes(issuer, self.hash_algorithm))


class MockOCSPResponder:
    """A threaded OCSP responder for the CAs of the configured certificate chain."""

    def __init__(self, port: int = 19080, cert_status: str = "good", revoked_serials=(), issuers=None):
        """
        cert_status: the status it gives every certificate it is asked about: "good", "revoked" or
            "unknown".
        revoked_serials: serial numbers of certificates it answers are revoked, whatever cert_status
            says.
        issuers: (certificate, private key) of each CA it answers for. Default: the root and the
            sub-CA of the configured chain.
        """
        if cert_status not in _CERT_STATUSES:
            raise ValueError(f"cert_status must be one of {sorted(_CERT_STATUSES)}, not {cert_status!r}")
        self.port = port
        self.cert_status = cert_status
        self.revoked_serials = set(revoked_serials)
        if issuers is None:
            issuers = [(contract_pki.load_certificate(name), contract_pki.load_private_key(name))
                       for name in (contract_pki.ROOT_CA, contract_pki.SUB_CA)]
        self.issuers = issuers
        self.requests = []
        self.requests_received = 0
        self._server = None
        self._thread = None

    def response_to(self, request_der: bytes) -> bytes:
        """The DER encoded OCSP response to a DER encoded OCSP request."""
        try:
            request = ocsp.load_der_ocsp_request(request_der)
        except ValueError:
            return _unsuccessful(ocsp.OCSPResponseStatus.MALFORMED_REQUEST)
        self.requests.append(ReceivedOCSPRequest(
            request.hash_algorithm, request.issuer_name_hash, request.issuer_key_hash, request.serial_number))

        cert_id_issuer = (request.issuer_name_hash, request.issuer_key_hash)
        signer = next(((certificate, key) for certificate, key in self.issuers
                       if _issuer_hashes(certificate, request.hash_algorithm) == cert_id_issuer), None)
        if signer is None:
            return _unsuccessful(ocsp.OCSPResponseStatus.UNAUTHORIZED)
        signer_certificate, signer_key = signer

        revoked = self.cert_status == 'revoked' or request.serial_number in self.revoked_serials
        now = datetime.now(timezone.utc)
        builder = ocsp.OCSPResponseBuilder().add_response_by_hash(
            issuer_name_hash=request.issuer_name_hash,
            issuer_key_hash=request.issuer_key_hash,
            serial_number=request.serial_number,
            algorithm=request.hash_algorithm,
            cert_status=ocsp.OCSPCertStatus.REVOKED if revoked else _CERT_STATUSES[self.cert_status],
            this_update=now - timedelta(minutes=5),
            next_update=now + timedelta(days=1),
            revocation_time=now - timedelta(days=1) if revoked else None,
            revocation_reason=x509.ReasonFlags.cessation_of_operation if revoked else None,
        ).responder_id(ocsp.OCSPResponderEncoding.HASH, signer_certificate)
        if signer_certificate.issuer != signer_certificate.subject:
            # A sub-CA: the CSMS knows the root, not the sub-CA.
            builder = builder.certificates([signer_certificate])
        try:
            nonce = request.extensions.get_extension_for_class(x509.OCSPNonce).value.nonce
            builder = builder.add_extension(x509.OCSPNonce(nonce), critical=False)
        except x509.ExtensionNotFound:
            pass
        return builder.sign(signer_key, hashes.SHA256()).public_bytes(serialization.Encoding.DER)

    def start(self):
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                parent.requests_received += 1
                body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                response = parent.response_to(body)
                self.send_response(200)
                self.send_header('Content-Type', 'application/ocsp-response')
                self.send_header('Content-Length', str(len(response)))
                self.end_headers()
                self.wfile.write(response)

            def log_message(self, format, *args):
                pass  # suppress request logging

        self._server = LocalHTTPServer(('localhost', self.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._thread.join(timeout=5)
            self._server = None
            self._thread = None
