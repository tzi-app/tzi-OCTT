"""
Test case name      Reset EVSE - Without ongoing transaction
Test case Id        TC_B_25_CSMS
Use case Id(s)      B11
Requirement(s)      B11.FR.04

Requirement Details:
    B11.FR.04: The Charging Station SHALL send a NotifyReportRequest for each component-variable combination that changed.
        Precondition: B11.FR.03
System under test   CSMS

Description         This test case covers how the CSMS can request the Charging Station to reset an EVSE by
                    sending a ResetRequest without any ongoing transaction. This could for example be necessary
                    if the Charging Station is not functioning correctly.
Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP specification.

Prerequisite(s)     N/a

Test Scenario
Manual Action: Request the CSMS to reboot an EVSE with status OnIdle
1. The CSMS sends a ResetRequest with status OnIdle and evseID <Configured evseId>
2. The OCTT responds with a ResetResponse with status Accepted

Tool validations
* Step 1:
    Message: ResetRequest
    - type OnIdle
    - evseId <Configured evseId>

Post scenario validations:
    - N/a
"""

import asyncio
import pytest
import os
import logging
from ocpp.v201.enums import (
    RegistrationStatusEnumType, ConnectorStatusEnumType, ResetStatusEnumType
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP_B']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_25(connection):
    """Reset EVSE - Without ongoing transaction: CSMS resets specific EVSE."""
    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    cp._reset_response_status = ResetStatusEnumType.accepted
    start_task = asyncio.create_task(cp.start())

    # Boot and establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Step 1-2: Wait for CSMS to send ResetRequest with evseId
    await asyncio.wait_for(
        cp._received_reset.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._reset_data is not None
    assert cp._reset_data['type'] == 'OnIdle', \
        f"Expected OnIdle reset type, got: {cp._reset_data['type']}"
    assert cp._reset_data['evse_id'] == CONFIGURED_EVSE_ID, \
        f"Expected evseId {CONFIGURED_EVSE_ID}, got: {cp._reset_data['evse_id']}"
    logging.info(f"Received ResetRequest for EVSE: type={cp._reset_data['type']}, "
                 f"evseId={cp._reset_data['evse_id']}")

    start_task.cancel()
