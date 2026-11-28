"""
Test case name      Cold Boot Charging Station - Pending/Rejected - SecurityError
Test case Id        TC_B_30_CSMS
Use case Id(s)      B02/B03
Requirement(s)      B02.FR.09, B03.FR.07

Requirement Details:
    B02.FR.09: The CSMS SHALL respond with RPC Framework: CALLERROR: SecurityError.
        Precondition: The Charging Station has received a BootNotificationResponse with status Pending AND the
                      Charging Station sends a RPC Framework: CALL message that is NOT a
                      BootNotificationRequest or a message triggered by one of the following messages:
                      TriggerMessageRequest, GetBaseReportRequest, GetReportRequest.
        Note: The Charging Station is not allowed to initiate sending other messages before being accepted.
    B03.FR.07: CSMS SHALL respond with RPC Framework: CALLERROR: SecurityError.
        Precondition: B03.FR.03 AND Charging Station sends a message that is not a BootNotificationRequest
System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about
                    the Charging Station to the CSMS on startup AND it allows the Charging Station to request
                    whether it is allowed to start sending other OCPP messages. The CSMS may respond to the
                    BootNotificationRequest with status Pending or Rejected. During this state, the Charging
                    Station is not allowed to send RPC Framework: CALL message that is NOT a
                    BootNotificationRequest or in case of status Pending, a message triggered by one of the
                    following messages: TriggerMessageRequest, GetBaseReportRequest, GetReportRequest.

Purpose             To verify whether the CSMS is able to handle unauthorized messages from the Charging
                    Station by responding with a SecurityError.

Prerequisite(s)     The CSMS is configured to first respond to a BootNotificationRequest with status Pending
                    or Rejected.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a BootNotificationRequest with:
    - reason PowerUp
    - chargingStation.model <Configured model>
    - chargingStation.vendorName <Configured vendorName>
2. The CSMS responds with a BootNotificationResponse
3. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest with:
    - connectorStatus Available
    Message: NotifyEventRequest with:
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
4. The CSMS responds with RPC Framework: CALLERROR: SecurityError.

Tool validations
* Step 2:
    Message: BootNotificationResponse
    - status Pending OR Rejected

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.exceptions import SecurityError

from charge_point import CONFIGURED_CONNECTOR_ID, CONFIGURED_NUMBER_OF_EVSES, TziChargePoint21
from ocpp_messages import utc_now_iso
from trigger import set_pending_boot
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_30(connection):
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

        # 3. The Test System notifies the CSMS about the current state of all connectors.
        #    StatusNotificationRequest - connectorStatus Available
        #    NotifyEventRequest - trigger Delta, actualValue "Available",
        #                         component.name "Connector", variable.name "AvailabilityState"
        # 4. The CSMS responds with RPC Framework: CALLERROR: SecurityError.
        for evse_id in range(1, CONFIGURED_NUMBER_OF_EVSES + 1):
            with pytest.raises(SecurityError):
                await cp.send_status_notification(CONFIGURED_CONNECTOR_ID, 'Available', evse_id=evse_id)
            with pytest.raises(SecurityError):
                await cp.send_notify_event([{
                    'event_id': evse_id,
                    'timestamp': utc_now_iso(),
                    'trigger': 'Delta',
                    'actual_value': 'Available',
                    'event_notification_type': 'HardWiredNotification',
                    'component': {
                        'name': 'Connector',
                        'evse': {'id': evse_id, 'connector_id': CONFIGURED_CONNECTOR_ID},
                    },
                    'variable': {'name': 'AvailabilityState'},
                }])
    finally:
        # The CSMS accepts the station again, so that other tests are not affected
        await set_pending_boot(BASIC_AUTH_CP, pending=False)

    start_task.cancel()
