"""
TC_N_36 - Retrieve Log Information - Second Request
Use case: N01 | Requirements: N/a
System under test: CSMS

Description:
    The CSMS sends two GetLogRequests. The first is in progress (Uploading), then
    a second GetLogRequest is sent. The first gets AcceptedCanceled status, and then
    the second proceeds normally through Uploading to Uploaded.

Purpose:
    To verify if the CSMS is able to send a second GetLogRequest while a first is
    still in progress, and that the Charging Station correctly cancels the first
    and proceeds with the second.

Main:
    1. CSMS sends GetLogRequest
    2. OCTT responds GetLogResponse with status = Accepted
    3. OCTT sends LogStatusNotificationRequest with status = Uploading, requestId = same as Step 1
    4. CSMS responds LogStatusNotificationResponse
    5. CSMS sends GetLogRequest (second request)
    6. OCTT responds GetLogResponse with status = AcceptedCanceled
    7. OCTT sends LogStatusNotificationRequest with status = AcceptedCanceled, requestId = same as Step 1
    8. CSMS responds LogStatusNotificationResponse
    9. OCTT sends LogStatusNotificationRequest with status = Uploading, requestId = same as Step 5
    10. CSMS responds LogStatusNotificationResponse
    11. OCTT sends LogStatusNotificationRequest with status = Uploaded, requestId = same as Step 5
    12. CSMS responds LogStatusNotificationResponse

Tool validations:
    N/a

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CSMS_ACTION_TIMEOUT       - Seconds to wait for CSMS action (default 30)
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201 import call as ocpp_call
from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    LogStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_n_36():
    """Retrieve Log Information - Second Request."""
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)

    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
    )
    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(CONNECTOR_ID, ConnectorStatusEnumType.available)

    # Step 1-2: Wait for CSMS to send first GetLogRequest
    await asyncio.wait_for(
        cp._received_get_log.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_log_data is not None
    request_id_1 = cp._get_log_data['request_id']
    assert request_id_1 is not None, "First GetLogRequest must contain a requestId"

    logging.info(f"TC_N_36 step 1-2 completed: First GetLogResponse Accepted, requestId={request_id_1}")

    # Step 3-4: OCTT sends LogStatusNotificationRequest (status=Uploading) for first request
    payload = ocpp_call.LogStatusNotification(status='Uploading', request_id=request_id_1)
    resp = await cp.call(payload)
    assert resp is not None

    logging.info("TC_N_36 step 3-4 completed: LogStatusNotification Uploading for first request")

    # Prepare for second GetLogRequest: respond with AcceptedCanceled
    cp._received_get_log.clear()
    cp._get_log_response_status = LogStatusEnumType.accepted_canceled

    # Step 5-6: Wait for CSMS to send second GetLogRequest
    await asyncio.wait_for(
        cp._received_get_log.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_log_data is not None
    request_id_2 = cp._get_log_data['request_id']
    assert request_id_2 is not None, "Second GetLogRequest must contain a requestId"

    logging.info(f"TC_N_36 step 5-6 completed: Second GetLogResponse AcceptedCanceled, requestId={request_id_2}")

    # Step 7-8: OCTT sends LogStatusNotificationRequest (status=AcceptedCanceled) for first request
    payload = ocpp_call.LogStatusNotification(status='AcceptedCanceled', request_id=request_id_1)
    resp = await cp.call(payload)
    assert resp is not None

    logging.info("TC_N_36 step 7-8 completed: LogStatusNotification AcceptedCanceled for first request")

    # Step 9-10: OCTT sends LogStatusNotificationRequest (status=Uploading) for second request
    payload = ocpp_call.LogStatusNotification(status='Uploading', request_id=request_id_2)
    resp = await cp.call(payload)
    assert resp is not None

    logging.info("TC_N_36 step 9-10 completed: LogStatusNotification Uploading for second request")

    # Step 11-12: OCTT sends LogStatusNotificationRequest (status=Uploaded) for second request
    payload = ocpp_call.LogStatusNotification(status='Uploaded', request_id=request_id_2)
    resp = await cp.call(payload)
    assert resp is not None

    logging.info("TC_N_36 completed successfully")
    start_task.cancel()
    await ws.close()
