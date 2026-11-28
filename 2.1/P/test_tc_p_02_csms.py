"""
Test case name      Data Transfer to the CSMS - Rejected / Unknown VendorId / Unknown MessageId
Test case Id        TC_P_02_CSMS
Use case Id(s)      P02
Requirement(s)      P02.FR.06, P02.FR.07

Requirement Details:
    P02.FR.06: The recipient SHALL return a status UnknownVendor.
        Precondition: If the recipient of the request has no implementation for the specific vendorId.
    P02.FR.07: The recipient SHALL return status UnknownMessageId.
        Precondition: Upon receipt of DataTransferRequest and in case of a messageId mismatch (if used).
System under test   CSMS

Description         The DataTransfer message to send information for functions that are not supported by OCPP.

Purpose             To verify whether the CSMS is able to handle receiving a DataTransferRequest, even if it
                    does not support any vendor-specific implementations.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a DataTransferRequest with
    - vendorId <Configured vendorId>
    - messageId <Configured messageId>
2. The CSMS responds with a DataTransferResponse

Tool validations
* Step 2:
    Message: DataTransferResponse
    - status must be UnknownVendorId OR UnknownMessageId OR Rejected (Rejected will also be allowed, because
      there are implementers that like to just reject the message when the Charging Station does not support
      any vendor-specific features.

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_VENDOR_ID = os.environ['CONFIGURED_VENDOR_ID']
CONFIGURED_MESSAGE_ID = os.environ['CONFIGURED_MESSAGE_ID']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_p_02(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The Test System sends a DataTransferRequest with
    #    - vendorId <Configured vendorId>
    #    - messageId <Configured messageId>
    # 2. The CSMS responds with a DataTransferResponse
    response = await cp.send_data_transfer(CONFIGURED_VENDOR_ID, message_id=CONFIGURED_MESSAGE_ID)
    # status must be UnknownVendorId OR UnknownMessageId OR Rejected (Rejected will also be
    # allowed, because there are implementers that like to just reject the message when the
    # Charging Station does not support any vendor-specific features.)
    assert response.status in ('UnknownVendorId', 'UnknownMessageId', 'Rejected'), \
        f"Expected DataTransferResponse.status UnknownVendorId, UnknownMessageId or Rejected, " \
        f"got {response.status}"

    start_task.cancel()
