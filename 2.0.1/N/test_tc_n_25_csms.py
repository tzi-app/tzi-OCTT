"""
TC_N_25 - Retrieve Log Information - Diagnostics Log - Success
Use case: N01 | Requirements: N/a
System under test: CSMS

Description:
    The CSMS can request a Charging Station to upload a file with log information to a given
    location (URL). The Charging Station successfully uploads a log file and gives information
    about the status of the upload by sending status notifications to the CSMS.

Purpose:
    To verify if the CSMS is able to request a charging station to successfully upload a log.

Main:
    1. CSMS sends GetLogRequest with logType = DiagnosticsLog
    2. OCTT responds GetLogResponse with status = Accepted
    3. OCTT sends LogStatusNotificationRequest with status = Uploading, requestId = same as GetLogRequest
    4. CSMS responds LogStatusNotificationResponse
    5. OCTT sends LogStatusNotificationRequest with status = Uploaded, requestId = same as GetLogRequest
    6. CSMS responds LogStatusNotificationResponse

Tool validations:
    * Step 1: logType = DiagnosticsLog

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
async def test_tc_n_25():
    """Retrieve Log Information - Diagnostics Log - Success."""
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

    # Step 1-2: Wait for CSMS to send GetLogRequest
    await asyncio.wait_for(
        cp._received_get_log.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._get_log_data is not None
    log_type = cp._get_log_data['log_type']

    # Tool validation Step 1: logType = DiagnosticsLog
    assert log_type == 'DiagnosticsLog', \
        f"Expected logType=DiagnosticsLog, got {log_type}"

    request_id = cp._get_log_data['request_id']
    assert request_id is not None, "GetLogRequest must contain a requestId"

    logging.info(f"TC_N_25 step 1-2 completed: GetLogResponse Accepted, requestId={request_id}")

    # Step 3-4: OCTT sends LogStatusNotificationRequest (status=Uploading)
    payload = ocpp_call.LogStatusNotification(status='Uploading', request_id=request_id)
    resp = await cp.call(payload)
    assert resp is not None

    logging.info("TC_N_25 step 3-4 completed: LogStatusNotification Uploading")

    # Step 5-6: OCTT sends LogStatusNotificationRequest (status=Uploaded)
    payload = ocpp_call.LogStatusNotification(status='Uploaded', request_id=request_id)
    resp = await cp.call(payload)
    assert resp is not None

    logging.info("TC_N_25 completed successfully")
    start_task.cancel()
    await ws.close()
