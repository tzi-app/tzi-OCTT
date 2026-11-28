"""
Test case name      Reset Charging Station - Without ongoing transaction - OnIdle
Test case Id        TC_B_20_CSMS
Use case Id(s)      B11
Requirement(s)      B11.FR.04

Requirement Details:
    B11.FR.04: The Charging Station SHALL proceed as described in use case B01 - Cold Boot Charging Station.
        Precondition: B11.FR.03
System under test   CSMS

Description         This test case covers how the CSMS can request the Charging Station to reset itself by
                    sending a ResetRequest without any ongoing transaction. This could for example be
                    necessary if the Charging Station is not functioning correctly.

Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP
                    specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to reboot the Charging Station with type _OnIdle

1. The CSMS sends a ResetRequest
2. The Test System responds with a ResetResponse with status Accepted
3. The Test System sends a BootNotificationRequest
4. The CSMS responds with a BootNotificationResponse
5. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
6. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message ResetRequest
    - evseId must be omitted
* Step 4:
    Message BootNotificationResponse
    - status Accepted

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


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_20(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request the CSMS to reboot the Charging Station with type OnIdle
    # 1. The CSMS sends a ResetRequest
    # 2. The Test System responds with a ResetResponse with status Accepted
    reset_request = await cp.wait_for_request(
        'Reset', manual_action=reset(BASIC_AUTH_CP, 'OnIdle'))
    assert reset_request.evse_id is None, \
        f"ResetRequest.evseId must be omitted, got: {reset_request.evse_id}"

    # 3. The Test System sends a BootNotificationRequest
    # 4. The CSMS responds with a BootNotificationResponse
    boot_response = await cp.send_boot_notification(reason='RemoteReset')
    assert boot_response.status == 'Accepted', \
        f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

    # 5. The Test System notifies the CSMS about the current state of all connectors.
    #    StatusNotificationRequest - connectorStatus Available
    #    NotifyEventRequest - trigger Delta, actualValue "Available",
    #                         component.name "Connector", variable.name "AvailabilityState"
    # 6. The CSMS responds accordingly.
    await cp.send_all_connectors_status('Available')

    start_task.cancel()
