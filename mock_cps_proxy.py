"""
Minimal mock CPS (Certificate Provisioning Service) proxy for M26/M28 tests.

Returns a fixed Accepted response with a dummy exiResponse for any
Get15118EVCertificate proxy request from the CSMS.

The CSMS POSTs JSON: {stationId, chargePointId, request: {action, iso15118SchemaVersion, exiRequest}}
and expects back:   {status, exiResponse, statusInfo?}

Uses only the standard library (http.server + threading) — no extra deps.

Usage:
    proxy = MockCpsProxy(port=19081)
    proxy.start()
    ...
    proxy.stop()
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


class MockCpsProxy:
    """A threaded mock CPS proxy that returns Accepted with a dummy exiResponse."""

    def __init__(self, port: int = 19081):
        self.port = port
        self._server = None
        self._thread = None
        self.requests_received = 0

    def start(self):
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                parent.requests_received += 1
                response = json.dumps({
                    "status": "Accepted",
                    "exiResponse": "dGVzdEVYSVJlc3BvbnNlRGF0YQ==",
                }).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(response)))
                self.end_headers()
                self.wfile.write(response)

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
