"""
Test case name      Cold Boot Charging Station - Pending/Rejected - TriggerMessage
Test case Id        TC_B_31_CSMS
Use case Id(s)      B02, F06
Requirement(s)      N/a
System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about the
                    Charging Station to the CSMS on startup AND it allows the Charging Station to request whether
                    it is allowed to start sending other OCPP messages.
Purpose             To verify whether the CSMS is able to send a TriggerMessageRequest to trigger a
                    BootNotificationRequest, before the interval expired.

Prerequisite(s)     The CSMS is configured to first respond to a BootNotificationRequest with status Pending or Rejected.

Test Scenario
1. The OCTT sends a BootNotificationRequest with reason PowerUp
2. The CSMS responds with a BootNotificationResponse (status: Pending or Rejected)
3. The CSMS sends a TriggerMessageRequest (requestedMessage: BootNotification)
4. The OCTT responds with a TriggerMessageResponse (status: Accepted)
5. The OCTT sends a BootNotificationRequest with reason Triggered
6. The CSMS responds with a BootNotificationResponse (status: Accepted)
7. The OCTT notifies the CSMS about the current state of all connectors.
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
import pytest
import os
import logging
from ocpp.v201.enums import (
    RegistrationStatusEnumType, ConnectorStatusEnumType
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, validate_schema

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP_B']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_31(connection):
    """Cold Boot CS - Pending/Rejected - TriggerMessage: CSMS triggers BootNotification."""
    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: BootNotification - expect Pending or Rejected
    boot_response = await cp.send_boot_notification()
    assert boot_response is not None
    assert validate_schema(data=boot_response, schema_file_name='BootNotificationResponse.json')
    assert boot_response.status in (
        RegistrationStatusEnumType.pending,
        RegistrationStatusEnumType.rejected,
    ), f"Expected Pending or Rejected, got: {boot_response.status}"

    # Step 3-4: Wait for CSMS to send TriggerMessageRequest (BootNotification)
    await asyncio.wait_for(
        cp._received_trigger_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    assert cp._trigger_message_data == 'BootNotification', \
        f"Expected TriggerMessage for BootNotification, got: {cp._trigger_message_data}"

    # Step 5-6: Send BootNotification with reason Triggered
    boot_response = await cp.send_boot_notification_with_reason('Triggered')
    assert boot_response is not None
    assert validate_schema(data=boot_response, schema_file_name='BootNotificationResponse.json')
    assert boot_response.status == RegistrationStatusEnumType.accepted

    # Step 7-8: Notify CSMS about connector states
    await cp.send_status_notification(1, ConnectorStatusEnumType.available)
    await cp.send_notify_event([{
        'event_id': 1,
        'timestamp': '2024-01-01T00:00:00Z',
        'trigger': 'Delta',
        'actual_value': 'Available',
        'event_notification_type': 'HardWiredNotification',
        'component': {'name': 'Connector'},
        'variable': {'name': 'AvailabilityState'},
    }])

    start_task.cancel()
