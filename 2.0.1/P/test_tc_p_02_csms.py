"""
TC_P_02 - Data Transfer to the CSMS - Rejected / Unknown VendorId / Unknown MessageId
Use case: P02 | Requirements: P02.FR.06, P02.FR.07
P02.FR.06: If the recipient of the request has no implementation for the specific vendorId, the recipient SHALL return a status UnknownVendor.
    Precondition: If the recipient of the request has no implementation for the specific vendorId.
P02.FR.07: Upon receipt of DataTransferRequest and in case of a messageId mismatch (if used). The recipient SHALL return status UnknownMessageId.
    Precondition: Upon receipt of DataTransferRequest and in case of a messageId mismatch (if used).
System under test: CSMS

Description:
    The DataTransfer message to send information for functions that are not
    supported by OCPP.

Purpose:
    To verify whether the CSMS is able to handle receiving a DataTransferRequest,
    even if it does not support any vendor-specific implementations.

Main:
    1. OCTT sends DataTransferRequest with vendorId and messageId
    2. CSMS responds with DataTransferResponse

Tool validations:
    * Step 2: DataTransferResponse
      - status must be UnknownVendorId OR UnknownMessageId OR Rejected

Configuration:
    CSMS_ADDRESS              - WebSocket URL of the CSMS
    BASIC_AUTH_CP             - Charge Point identifier
    BASIC_AUTH_CP_PASSWORD    - Charge Point password
    CONFIGURED_CONNECTOR_ID   - Connector id (default 1)
    CONFIGURED_VENDOR_ID      - Vendor id for DataTransfer (default tzi.app)
    CONFIGURED_MESSAGE_ID     - Message id for DataTransfer (default TestMessage)
"""
import asyncio
import logging
import os
import sys
import time

import pytest
import websockets

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocpp.v201.enums import (
    RegistrationStatusEnumType,
    ConnectorStatusEnumType,
    DataTransferStatusEnumType,
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
CONFIGURED_VENDOR_ID = os.environ['CONFIGURED_VENDOR_ID']
CONFIGURED_MESSAGE_ID = os.environ['CONFIGURED_MESSAGE_ID']

ALLOWED_STATUSES = {
    DataTransferStatusEnumType.unknown_vendor_id,
    DataTransferStatusEnumType.unknown_message_id,
    DataTransferStatusEnumType.rejected,
}


@pytest.mark.asyncio
async def test_tc_p_02():
    """Data Transfer to the CSMS - Rejected / Unknown VendorId / Unknown MessageId."""
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

    # Step 1-2: Send DataTransferRequest, CSMS responds with DataTransferResponse
    response = await cp.send_data_transfer(
        vendor_id=CONFIGURED_VENDOR_ID,
        message_id=CONFIGURED_MESSAGE_ID,
    )
    assert response is not None
    assert response.status in ALLOWED_STATUSES, (
        f"Expected status to be one of {ALLOWED_STATUSES}, got {response.status}"
    )

    logging.info(f"TC_P_02 completed successfully - status: {response.status}")
    start_task.cancel()
    await ws.close()
