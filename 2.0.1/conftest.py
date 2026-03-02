import os
import sys
from pathlib import Path
import pytest_asyncio
import websockets
from websockets import InvalidStatusCode
from dataclasses import dataclass
import time

# Keep imports stable after test tree moves:
# allow resolving helper modules from both repo root and version folder.
_VERSION_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _VERSION_ROOT.parent
for _path in (str(_VERSION_ROOT), str(_PROJECT_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from utils import build_default_ssl_context

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']


@dataclass
class MockConnection:
    open: bool
    status_code: int

@pytest_asyncio.fixture
async def connection(request):
    cp_name, headers = request.param
    try:
        uri = f'{CSMS_ADDRESS}/{cp_name}'
        ssl_ctx = build_default_ssl_context() if uri.startswith('wss://') else None
        ws = await websockets.connect(uri=uri,
                                      subprotocols=['ocpp2.0.1'],
                                      extra_headers=headers,
                                      ssl=ssl_ctx)
    except InvalidStatusCode as e:
        yield MockConnection(open=False, status_code=e.status_code)
        return

    # Some delay is required by some CSMS prior to being able to handle data sent
    time.sleep(0.5)
    yield ws

    await ws.close()
