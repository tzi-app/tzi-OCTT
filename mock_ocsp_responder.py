"""
Minimal mock OCSP responder for C50/C51 tests.

Builds valid DER-encoded OCSP responses per RFC 6960 so the CSMS can parse
them with its own ASN.1 reader.  No real crypto — just enough structure to
satisfy the DER parser in certificate_management.rs::is_ocsp_response_good().

Uses only the standard library (http.server + threading) — no extra deps.

Usage:
    responder = MockOCSPResponder(port=19080, cert_status="good")
    responder.start()
    ...
    responder.stop()
"""

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


# ---------------------------------------------------------------------------
# DER helpers
# ---------------------------------------------------------------------------

def _der_length(length: int) -> bytes:
    if length < 0x80:
        return bytes([length])
    elif length < 0x100:
        return bytes([0x81, length])
    else:
        return bytes([0x82, (length >> 8) & 0xFF, length & 0xFF])


def _der_sequence(content: bytes) -> bytes:
    return b'\x30' + _der_length(len(content)) + content


def _der_octet_string(data: bytes) -> bytes:
    return b'\x04' + _der_length(len(data)) + data


def _der_enumerated(value: int) -> bytes:
    return b'\x0a\x01' + bytes([value])


def _der_oid(oid_bytes: bytes) -> bytes:
    return b'\x06' + _der_length(len(oid_bytes)) + oid_bytes


def _der_generalized_time(time_str: str = "20260101000000Z") -> bytes:
    encoded = time_str.encode('ascii')
    return b'\x18' + _der_length(len(encoded)) + encoded


def _der_context_explicit(tag: int, content: bytes) -> bytes:
    t = 0xA0 | (tag & 0x1F)
    return bytes([t]) + _der_length(len(content)) + content


def _der_context_implicit(tag: int, content: bytes) -> bytes:
    t = 0x80 | (tag & 0x1F)
    return bytes([t]) + _der_length(len(content)) + content


# ---------------------------------------------------------------------------
# OCSP response builder
# ---------------------------------------------------------------------------

# OID for id-pkix-ocsp-basic (1.3.6.1.5.5.7.48.1.1)
_BASIC_OCSP_RESPONSE_OID = bytes([0x2B, 0x06, 0x01, 0x05, 0x05, 0x07, 0x30, 0x01, 0x01])

# OID for SHA-256 (2.16.840.1.101.3.4.2.1)
_SHA256_OID = bytes([0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01])


def build_ocsp_response(cert_status: str = "good") -> bytes:
    """
    Build a minimal but structurally valid DER-encoded OCSP response.

    cert_status: "good" | "revoked" | "unknown"
    """
    # certStatus CHOICE: good [0] IMPLICIT NULL, revoked [1], unknown [2]
    if cert_status == "good":
        cert_status_der = _der_context_implicit(0, b'')
    elif cert_status == "revoked":
        # revoked [1] IMPLICIT SEQUENCE { revocationTime GeneralizedTime }
        revocation_time = _der_generalized_time("20250101000000Z")
        cert_status_der = _der_context_explicit(1, revocation_time)
    else:
        cert_status_der = _der_context_implicit(2, b'')

    # CertID: hashAlgorithm + issuerNameHash + issuerKeyHash + serialNumber
    hash_algorithm = _der_sequence(_der_oid(_SHA256_OID) + b'\x05\x00')
    issuer_name_hash = _der_octet_string(b'\x00' * 32)
    issuer_key_hash = _der_octet_string(b'\x00' * 32)
    serial_number = b'\x02\x01\x01'  # INTEGER 1
    cert_id = _der_sequence(hash_algorithm + issuer_name_hash + issuer_key_hash + serial_number)

    # thisUpdate GeneralizedTime
    this_update = _der_generalized_time("20260101000000Z")

    # SingleResponse: certID + certStatus + thisUpdate
    single_response = _der_sequence(cert_id + cert_status_der + this_update)

    # responses: SEQUENCE OF SingleResponse
    responses = _der_sequence(single_response)

    # responderID: [1] EXPLICIT (byName) — use a dummy Name
    responder_name = _der_sequence(b'')
    responder_id = _der_context_explicit(1, responder_name)

    # producedAt
    produced_at = _der_generalized_time("20260101000000Z")

    # tbsResponseData: responderID + producedAt + responses
    tbs_response_data = _der_sequence(responder_id + produced_at + responses)

    # signatureAlgorithm
    sig_alg = _der_sequence(_der_oid(_SHA256_OID) + b'\x05\x00')

    # signature BIT STRING (dummy)
    signature = b'\x03\x03\x00\x00\x00'

    # BasicOCSPResponse: tbsResponseData + signatureAlgorithm + signature
    basic_ocsp_response = _der_sequence(tbs_response_data + sig_alg + signature)

    # ResponseBytes: responseType OID + response OCTET STRING
    response_bytes = _der_sequence(
        _der_oid(_BASIC_OCSP_RESPONSE_OID) + _der_octet_string(basic_ocsp_response)
    )

    # OCSPResponse: responseStatus ENUMERATED(0=successful) + [0] EXPLICIT responseBytes
    ocsp_response = _der_sequence(
        _der_enumerated(0) + _der_context_explicit(0, response_bytes)
    )

    return ocsp_response


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class MockOCSPResponder:
    """A threaded mock OCSP responder that returns a fixed cert status."""

    def __init__(self, port: int = 19080, cert_status: str = "good"):
        self.port = port
        self.cert_status = cert_status
        self._response_der = build_ocsp_response(cert_status)
        self._server = None
        self._thread = None
        self.requests_received = 0

    def start(self):
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                parent.requests_received += 1
                self.send_response(200)
                self.send_header('Content-Type', 'application/ocsp-response')
                self.send_header('Content-Length', str(len(parent._response_der)))
                self.end_headers()
                self.wfile.write(parent._response_der)

            def log_message(self, format, *args):
                pass  # suppress request logging

        self._server = HTTPServer(('localhost', self.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._thread.join(timeout=5)
            self._server = None
            self._thread = None
