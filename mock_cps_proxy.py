"""
Minimal mock CPS (Certificate Provisioning Service) proxy for M26/M28 tests.

Returns a fixed Accepted response with a dummy exiResponse for any
Get15118EVCertificate proxy request from the CSMS.

The CSMS POSTs JSON: {stationId, chargePointId, request: {action, iso15118SchemaVersion, exiRequest}}
and expects back:   {status, exiResponse, statusInfo?}

For ISO 15118-20 (OCPP 2.1, TC_M_100) the request also has maximumContractCertificateChains
and prioritizedEMAIDs, and the answer has remainingContracts.

Uses only the standard library (http.server + threading) — no extra deps.

Usage:
    proxy = MockCpsProxy(port=19081)
    proxy.start()
    ...
    proxy.stop()
"""

import json
import threading
from http.server import BaseHTTPRequestHandler

from utils import LocalHTTPServer


class MockCpsProxy:
    """A threaded mock CPS proxy that returns Accepted with a dummy exiResponse."""

    def __init__(self, port: int = 19081, contract_certificate_chains: int = None):
        """contract_certificate_chains: the number of contract certificate chains that the CPS
        has for the EV (ISO 15118-20). Each request then gets the next one, and the answer
        says in remainingContracts how many are left."""
        self.port = port
        self._server = None
        self._thread = None
        self.requests_received = 0
        self.requests = []
        self._contract_certificate_chains = contract_certificate_chains

    def start(self):
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                parent.requests_received += 1
                length = int(self.headers.get('Content-Length') or 0)
                try:
                    parent.requests.append(json.loads(self.rfile.read(length) or b'{}'))
                except ValueError:
                    parent.requests.append(None)
                answer = {
                    "status": "Accepted",
                    "exiResponse": "dGVzdEVYSVJlc3BvbnNlRGF0YQ==",
                }
                if parent._contract_certificate_chains is not None:
                    answer["remainingContracts"] = max(
                        parent._contract_certificate_chains - parent.requests_received, 0)
                response = json.dumps(answer).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
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
            self._thread.join(timeout=5)
            self._server = None
            self._thread = None
