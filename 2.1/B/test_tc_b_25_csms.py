"""
Test case name      Reset EVSE - Without ongoing transaction
Test case Id        TC_B_25_CSMS
Use case Id(s)      B11
Requirement(s)      B11.FR.04

Requirement Details:
    B11.FR.04: The Charging Station SHALL proceed as described in use case B01 - Cold Boot Charging Station.
        Precondition: B11.FR.03
System under test   CSMS

Description         This test case covers how the CSMS can request the Charging Station to reset an EVSE by
                    sending a ResetRequest without any ongoing transaction. This could for example be
                    necessary if the Charging Station is not functioning correctly.

Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP
                    specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to reboot an EVSE with status OnIdle

1. The CSMS sends a ResetRequest with:
    - status OnIdle
    - evseID <Configured evseId>
2. The Test System responds with a ResetResponse with status Accepted

Tool validations
* Step 1:
    Message ResetRequest
    - type OnIdle
    - evseId <Configured evseId>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import reset
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_25(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to reboot an EVSE with status OnIdle
    # 1. The CSMS sends a ResetRequest with status OnIdle and evseId <Configured evseId>
    # 2. The Test System responds with a ResetResponse with status Accepted
    reset_request = await cp.wait_for_request(
        'Reset', manual_action=reset(BASIC_AUTH_CP, 'OnIdle', evse_id=CONFIGURED_EVSE_ID))
    assert reset_request.type == 'OnIdle', \
        f"Expected ResetRequest.type OnIdle, got: {reset_request.type}"
    assert reset_request.evse_id == CONFIGURED_EVSE_ID, \
        f"Expected ResetRequest.evseId {CONFIGURED_EVSE_ID}, got: {reset_request.evse_id}"

    start_task.cancel()
