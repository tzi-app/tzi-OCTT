"""
Test case name      Cold Boot Charging Station - Pending/Rejected - TriggerMessage
Test case Id        TC_B_31_CSMS
Use case Id(s)      B02, F06
Requirement(s)      N/a
System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about
                    the Charging Station to the CSMS on startup AND it allows the Charging Station to request
                    whether it is allowed to start sending other OCPP messages.

Purpose             To verify whether the CSMS is able to send a TriggerMessageRequest to trigger a
                    BootNotificationRequest, before the interval expired.

Prerequisite(s)     The CSMS is configured to first respond to a BootNotificationRequest with status Pending
                    or Rejected.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a BootNotificationRequest
    - with reason PowerUp
    - chargingStation.model <Configured model>
    - chargingStation.vendorName <Configured vendorName>
2. The CSMS responds with a BootNotificationResponse
3. The CSMS sends a TriggerMessageRequest
4. The Test System responds with a TriggerMessageResponse
    - with status Accepted
5. The Test System sends a BootNotificationRequest
    - with reason Triggered
    - chargingStation.model <Configured model>
    - chargingStation.vendorName <Configured vendorName>
6. The CSMS responds with a BootNotificationResponse
7. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - with connectorStatus Available
    Message: NotifyEventRequest
    - with trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
8. The CSMS responds accordingly.

Tool validations
* Step 2:
    Message: BootNotificationResponse
    - status Pending OR Rejected
* Step 3:
    Message: TriggerMessageRequest
    - requestedMessage BootNotification
* Step 6:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from trigger import send_call, set_pending_boot
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_31(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: The CSMS is configured to first respond to a BootNotificationRequest with
    # status Pending or Rejected.
    await set_pending_boot(BASIC_AUTH_CP, pending=True)
    try:
        # 1. The Test System sends a BootNotificationRequest with reason PowerUp, the
        #    configured model and the configured vendorName
        # 2. The CSMS responds with a BootNotificationResponse
        boot_response = await cp.send_boot_notification(reason='PowerUp')
        assert boot_response.status in ('Pending', 'Rejected'), \
            f"Expected BootNotificationResponse.status Pending or Rejected, got {boot_response.status}"
    finally:
        # The CSMS accepts the station from here on.
        await set_pending_boot(BASIC_AUTH_CP, pending=False)

    # 3. The CSMS sends a TriggerMessageRequest
    # 4. The Test System responds with a TriggerMessageResponse with status Accepted
    trigger_message = await cp.wait_for_request(
        'TriggerMessage',
        manual_action=send_call(BASIC_AUTH_CP, 'TriggerMessage',
                                {'requestedMessage': 'BootNotification'}))
    assert trigger_message.requested_message == 'BootNotification', \
        f"Expected requestedMessage BootNotification, got: {trigger_message.requested_message}"

    # 5. The Test System sends a BootNotificationRequest with reason Triggered, the configured
    #    model and the configured vendorName
    # 6. The CSMS responds with a BootNotificationResponse
    boot_response = await cp.send_boot_notification(reason='Triggered')
    assert boot_response.status == 'Accepted', \
        f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

    # 7. The Test System notifies the CSMS about the current state of all connectors.
    #    StatusNotificationRequest - connectorStatus Available
    #    NotifyEventRequest - trigger Delta, actualValue "Available",
    #                         component.name "Connector", variable.name "AvailabilityState"
    # 8. The CSMS responds accordingly.
    await cp.send_all_connectors_status('Available')

    start_task.cancel()
