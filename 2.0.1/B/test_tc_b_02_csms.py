"""
Test case name      Cold Boot Charging Station - Pending
Test case Id        TC_B_02_CSMS
Use case Id(s)      B02
Requirement(s)      B02.FR.01, B02.FR.06
System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about the
                    Charging Station to the CSMS on startup AND it allows the Charging Station to request whether
                    it is allowed to start sending other OCPP messages. The CSMS may respond to the
                    BootNotificationRequest with status Pending. The Pending status can indicate that the CSMS
                    wants to retrieve or set certain information on the Charging Station before it will accept
                    the Charging Station.
Purpose             To verify whether the CSMS is able to accept the communications of a registered Charging Station.
Prerequisite(s)     The CSMS is configured to first respond to a BootNotificationRequest with status Pending.

Test Scenario
    Charging Station                                    CSMS
    1. BootNotificationRequest  ------>
       reason: PowerUp
       chargingStation.model: <Configured model>
       chargingStation.vendorName: <Configured vendorName>
                                                        2. BootNotificationResponse
                                                           status: Pending

    (wait interval seconds before retrying)
    Note: During this interval, the CSMS MAY send messages to retrieve information (B06, B07, B08)
    or change configuration via SetVariablesRequest (B05). The Test System will respond to these.

    3. BootNotificationRequest  ------>
       reason: PowerUp
       chargingStation.model: <Configured model>
       chargingStation.vendorName: <Configured vendorName>
                                                        4. BootNotificationResponse
                                                           status: Accepted

    5. StatusNotificationRequest  ------>
       connectorStatus: Available
       NotifyEventRequest  ------>
       trigger: Delta
       actualValue: "Available"
       component.name: "Connector"
       variable.name: "AvailabilityState"
                                                        6. CSMS responds accordingly.

Note(s):
- If the interval in the BootNotificationResponse equals 0, the Test System will wait
  <Configured heartbeatInterval> seconds, before sending another BootNotificationRequest.
- If the interval in the BootNotificationResponse > 0, the Test System will wait <Interval
  provided at the BootNotificationResponse> seconds, before sending another BootNotificationRequest.

Tool validations
* Step 2:
    Message: BootNotificationResponse
    - status Pending
* Step 4:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a
"""

import asyncio
import pytest
import os
import time

import websockets

from ocpp.v201.enums import RegistrationStatusEnumType, ConnectorStatusEnumType

from tzi_charge_point import TziChargePoint
from trigger import set_pending_boot
from utils import get_basic_auth_headers, validate_schema, build_default_ssl_context

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
async def test_tc_b_02():
    """Cold Boot Charging Station - Pending: CSMS first responds Pending, then Accepted."""
    # Pre-test: tell the CSMS to put this station into Pending mode
    await set_pending_boot(BASIC_AUTH_CP)

    # Connect to the CSMS
    uri = f'{CSMS_ADDRESS}/{BASIC_AUTH_CP}'
    headers = get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD)
    ssl_ctx = build_default_ssl_context() if uri.startswith('wss://') else None
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )
    time.sleep(0.5)
    assert ws.open

    cp = TziChargePoint(BASIC_AUTH_CP, ws)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: First BootNotification - expect Pending
    boot_response = await cp.send_boot_notification()
    assert boot_response is not None
    assert validate_schema(data=boot_response, schema_file_name='BootNotificationResponse.json')
    assert boot_response.status == RegistrationStatusEnumType.pending
    await set_pending_boot(BASIC_AUTH_CP, pending=False)

    # Wait for the interval specified by the CSMS before retrying
    interval = boot_response.interval if boot_response.interval > 0 else 10
    await asyncio.sleep(interval)

    # Step 3-4: Second BootNotification - expect Accepted
    boot_response = await cp.send_boot_notification()
    assert boot_response is not None
    assert validate_schema(data=boot_response, schema_file_name='BootNotificationResponse.json')
    assert boot_response.status == RegistrationStatusEnumType.accepted

    # Step 5-6: Notify CSMS about connector states
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
    await ws.close()