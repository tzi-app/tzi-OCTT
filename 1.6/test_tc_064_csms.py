"""
Test case name      Data Transfer to a Central System
Test case Id        TC_064_CSMS
Feature profile     Core  # NOTE: not explicitly in the test case document table (inferred from OCPP 1.6 spec -- to be verified)

Reference           CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf
                    Table 183, Section 3.20.1, p.157-158/176

Description         The Charge Point sends a vendor specific message to the Central System.

Purpose             To check whether the Central System can reject vendor specific messages.

Prerequisite(s)     The Central System does not support DataTransfer for a specific vendorId.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
1. The Charge Point (Tool) sends a DataTransfer.req message with a specific vendorId
   to the Charge Point.
        NOTE: The official doc (p.157) says "to the Charge Point" -- likely a typo,
        should be "to the Central System".

2. The Central System (SUT) responds with a DataTransfer.conf message.

Tool validations
* Step 2 (Central System side):
    (Message: DataTransfer.conf)
    - The status is Rejected OR UnknownMessageId OR UnknownVendorId

    Note: The status Accepted is allowed, but the vendor should be warned
    about this behaviour.

Expected result(s) / behaviour
    The Central System does not accept the DataTransfer.req.

Message Schemas (OCPP 1.6J):
    DataTransfer.req:
        - vendorId (required, string, maxLength 255): Identifies the vendor-specific implementation
        - messageId (optional, string, maxLength 50): Additional identification field
        - data (optional, string): Data without specified format

    DataTransfer.conf:
        - status (required, enum): Accepted | Rejected | UnknownMessageId | UnknownVendorId
        - data (optional, string): Data without specified format
"""

import asyncio
import logging
import os
import pytest

from ocpp.v16.enums import DataTransferStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

logger = logging.getLogger(__name__)

BASIC_AUTH_CP = os.environ['CP16_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_064(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: CP sends DataTransfer.req to CSMS
    response = await cp.send_data_transfer(vendor_id='TestVendor')
    assert response is not None
    assert response.status in (
        DataTransferStatus.rejected,
        DataTransferStatus.unknown_message_id,
        DataTransferStatus.unknown_vendor_id,
        DataTransferStatus.accepted,
    ), f"Unexpected DataTransfer status={response.status}"

    if response.status == DataTransferStatus.accepted:
        logger.warning(
            "WARNING: Central System accepted the DataTransfer for unsupported vendorId 'TestVendor'. "
            "Per test spec, status Accepted is allowed but the vendor should be warned about this behaviour."
        )

    start_task.cancel()
