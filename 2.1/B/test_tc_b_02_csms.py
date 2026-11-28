"""
Test case name      Cold Boot Charging Station - Pending
Test case Id        TC_B_02_CSMS
Use case Id(s)      B02
Requirement(s)      B02.FR.01, B02.FR.06

Requirement Details:
    B02.FR.01: The CSMS MAY send messages to retrieve information from the Charging Station (as described in
               use cases B06, B07, B08) or change its configuration by SetVariablesRequest (as described in
               use case B05). The Charging Station SHALL respond to these messages.
        Precondition: After the Charging Station received the Pending status.
        Note: The Pending status can thus indicate that the CSMS wants to retrieve or set certain information
              on the Charging Station before it will accept the Charging Station.
    B02.FR.06: The communication channel SHALL NOT be closed by either the Charging Station or the CSMS.
        Precondition: When the CSMS returns the Pending status
System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about
                    the Charging Station to the CSMS on startup AND it allows the Charging Station to request
                    whether it is allowed to start sending other OCPP messages. The CSMS may respond to the
                    BootNotificationRequest with status Pending. The Pending status can indicate that the CSMS
                    wants to retrieve or set certain information on the Charging Station before it will accept
                    the Charging Station.

Purpose             To verify whether the CSMS is able to accept the communications of a registered Charging
                    Station.

Prerequisite(s)     The CSMS is configured to first respond to a BootNotificationRequest with status Pending.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a BootNotificationRequest with:
    - reason PowerUp
    - chargingStation.model <Configured model>
    - chargingStation.vendorName <Configured vendorName>
2. The CSMS responds with a BootNotificationResponse

Note(s):
- If the interval in the BootNotificationResponse equals 0, the Test System will wait <Configured
  heartbeatInterval> seconds, before sending another BootNotificationRequest.
- If the interval in the BootNotificationResponse > 0, the Test System will wait <Interval provided at the
  BootNotificationResponse> seconds, before sending another BootNotificationRequest.
- During this interval, the CSMS may send messages to retrieve information from the Charging Station (as
  described in use cases B06, B07, B08) or change its configuration by SetVariablesRequest (as described in
  use case B05). The Test System will respond to these messages.

3. The Test System sends a BootNotificationRequest with:
    - reason PowerUp
    - chargingStation.model <Configured model>
    - chargingStation.vendorName <Configured vendorName>
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
* Step 2:
    Message: BootNotificationResponse
    - status Pending
* Step 3:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from trigger import set_pending_boot
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_HEARTBEAT_INTERVAL = int(os.environ['CONFIGURED_HEARTBEAT_INTERVAL'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_02(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Prerequisite: The CSMS is configured to first respond to a BootNotificationRequest with
    # status Pending.
    await set_pending_boot(BASIC_AUTH_CP, pending=True)
    try:
        # 1. The Test System sends a BootNotificationRequest with reason PowerUp, the
        #    configured model and the configured vendorName
        # 2. The CSMS responds with a BootNotificationResponse
        boot_response = await cp.send_boot_notification(reason='PowerUp')
        assert boot_response.status == 'Pending', \
            f"Expected BootNotificationResponse.status Pending, got {boot_response.status}"
    finally:
        # The CSMS accepts the station from here on.
        await set_pending_boot(BASIC_AUTH_CP, pending=False)

    # If the interval in the BootNotificationResponse equals 0, the Test System waits
    # <Configured heartbeatInterval> seconds before sending another BootNotificationRequest,
    # and otherwise the interval of the BootNotificationResponse. During this interval, the
    # CSMS may send messages to retrieve information from the Charging Station or to change
    # its configuration. The Test System responds to these messages.
    await asyncio.sleep(boot_response.interval or CONFIGURED_HEARTBEAT_INTERVAL)

    # 3. The Test System sends a BootNotificationRequest with reason PowerUp, the configured
    #    model and the configured vendorName
    # 4. The CSMS responds with a BootNotificationResponse
    boot_response = await cp.send_boot_notification(reason='PowerUp')
    assert boot_response.status == 'Accepted', \
        f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

    # 5. The Test System notifies the CSMS about the current state of all connectors.
    #    StatusNotificationRequest - connectorStatus Available
    #    NotifyEventRequest - trigger Delta, actualValue "Available",
    #                         component.name "Connector", variable.name "AvailabilityState"
    # 6. The CSMS responds accordingly.
    await cp.send_all_connectors_status('Available')

    start_task.cancel()
