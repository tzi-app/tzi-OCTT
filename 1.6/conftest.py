import os
import ssl
import sys
from pathlib import Path
import pytest
import pytest_asyncio
import websockets
from websockets import InvalidStatusCode
from dataclasses import dataclass
import time

_VERSION_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _VERSION_ROOT.parent
for _path in (str(_VERSION_ROOT), str(_PROJECT_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']


def pytest_addoption(parser):
    parser.addoption(
        '--log-messages',
        action='store_true',
        default=False,
        help='Log all incoming/outgoing OCPP messages during tests',
    )


def _build_ssl_context():
    """Build an SSL context for wss:// connections, skipping cert verification for local dev."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ca_cert = os.environ.get('TLS_CA_CERT')
    if ca_cert:
        ctx.load_verify_locations(ca_cert)
    else:
        ctx.verify_mode = ssl.CERT_NONE
    ctx.check_hostname = False
    return ctx


@dataclass
class MockConnection:
    open: bool
    status_code: int


@pytest_asyncio.fixture
async def connection(request):
    cp_name, headers = request.param
    try:
        uri = f'{CSMS_ADDRESS}/{cp_name}'
        ssl_ctx = _build_ssl_context() if uri.startswith('wss://') else None
        ws = await websockets.connect(uri=uri,
                                      subprotocols=['ocpp1.6'],
                                      extra_headers=headers,
                                      ssl=ssl_ctx)
    except InvalidStatusCode as e:
        yield MockConnection(open=False, status_code=e.status_code)
        return

    time.sleep(0.5)
    yield ws

    await ws.close()
