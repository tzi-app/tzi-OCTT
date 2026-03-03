"""
Test case name      Cold Boot Charging Station - Accepted
Test case Id        TC_B_01_CSMS
Use case Id(s)      B01
Requirement(s)      B01.FR.02

Requirement Details:
    B01.FR.02: The CSMS has received BootNotificationRequest from the Charging Station.
               The CSMS SHALL respond to indicate whether it will accept the Charging Station.
               Precondition: B01.FR.01 The CSMS has received BootNotificationRequest from the Charging Station.

System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about the
                    Charging Station to the CSMS on startup AND it allows the Charging Station to request whether
                    it is allowed to start sending other OCPP messages.

Purpose             To verify whether the CSMS is able to accept the communications of a registered Charging Station.

Prerequisite(s)     N/a

Test Scenario (Reusable State: Booted)
1. The OCTT sends a BootNotificationRequest with reason PowerUp
2. The CSMS responds with a BootNotificationResponse
3. The OCTT notifies the CSMS about the current state of all connectors.
4. The CSMS responds accordingly.

Tool validations
* Step 2:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a
"""

import asyncio
import pytest
import os

from ocpp.v201.enums import RegistrationStatusEnumType, ConnectorStatusEnumType

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, validate_schema

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_01(connection):
    """Cold Boot Charging Station - Accepted: Execute Reusable State Booted."""
    assert connection.open

    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: BootNotification with PowerUp reason
    boot_response = await cp.send_boot_notification()
    assert boot_response is not None
    assert validate_schema(data=boot_response, schema_file_name='BootNotificationResponse.json')
    assert boot_response.status == RegistrationStatusEnumType.accepted

    # Step 3-4: Notify CSMS about connector states
    status_response = await cp.send_status_notification(1, ConnectorStatusEnumType.available)
    assert status_response is not None

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
