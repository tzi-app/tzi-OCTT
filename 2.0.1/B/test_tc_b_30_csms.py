"""
Test case name      Cold Boot Charging Station - Pending/Rejected - SecurityError
Test case Id        TC_B_30_CSMS
Use case Id(s)      B02/B03
Requirement(s)      B02.FR.09, B03.FR.07

Requirement Details:
    B02.FR.09: The Charging Station has received a BootNotificationResponse with status Pending AND the Charging Station sends a RPC Framework: CALL message that is NOT a BootNotificationRequest or a message triggered by one of the following messages: TriggerMessageRequest,
        Precondition: The Charging Station has received a BootNotificationResponse with status Pending AND the Charging Station sends a RPC Framework: CALL message that is NOT a BootNotificationRequest or a message triggered by one of the following messages: TriggerMessageRequest, GetBaseReportRequest, GetReportRequest.
    B03.FR.07: B03.FR.03 AND Charging Station sends a message that is not a BootNotificationRequest
        Precondition: B03.FR.03 AND CSMS sends a message that is not a response to a BootNotificationRequest from Charging Station
System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about the
                    Charging Station to the CSMS on startup AND it allows the Charging Station to request whether
                    it is allowed to start sending other OCPP messages. The CSMS may respond to the
                    BootNotificationRequest with status Pending or Rejected. During this state, the Charging
                    Station is not allowed to send RPC Framework: CALL message that is NOT a BootNotificationRequest
                    or in case of status Pending, a message triggered by one of the following messages:
                    TriggerMessageRequest, GetBaseReportRequest, GetReportRequest.
Purpose             To verify whether the CSMS is able to handle unauthorized messages from the Charging Station by
                    responding with a SecurityError.

Prerequisite(s)     The CSMS is configured to first respond to a BootNotificationRequest with status Pending or Rejected.

Test Scenario
1. The OCTT sends a BootNotificationRequest with reason PowerUp
2. The CSMS responds with a BootNotificationResponse (status: Pending or Rejected)
3. The OCTT notifies the CSMS about the current state of all connectors.
4. The CSMS responds with RPC Framework: CALLERROR: SecurityError.

Tool validations
* Step 2:
    Message: BootNotificationResponse
    - status Pending OR Rejected

Post scenario validations:
    N/a
"""

import asyncio
import pytest
import os
import logging

from ocpp.v201.enums import RegistrationStatusEnumType, ConnectorStatusEnumType
from ocpp.exceptions import OCPPError

from tzi_charge_point import TziChargePoint
from trigger import set_pending_boot
from utils import get_basic_auth_headers, validate_schema

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_30(connection):
    """Cold Boot CS - Pending/Rejected - SecurityError: CSMS rejects unauthorized messages."""
    assert connection.open

    # Set pending provisioning so CSMS responds with Pending on boot
    await set_pending_boot(BASIC_AUTH_CP)

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

    # Step 3-4: Unauthorized StatusNotificationRequest and NotifyEventRequest should be rejected.
    security_error_received = False

    try:
        await cp.send_status_notification(1, ConnectorStatusEnumType.available)
    except OCPPError as e:
        logging.info(f"Received expected CALLERROR for StatusNotification: {e}")
        assert 'SecurityError' in str(e), f"Expected SecurityError, got: {e}"
        security_error_received = True

    try:
        await cp.send_notify_event([{
            'event_id': 1,
            'timestamp': '2024-01-01T00:00:00Z',
            'trigger': 'Delta',
            'actual_value': 'Available',
            'event_notification_type': 'HardWiredNotification',
            'component': {'name': 'Connector'},
            'variable': {'name': 'AvailabilityState'},
        }])
    except OCPPError as e:
        logging.info(f"Received expected CALLERROR for NotifyEvent: {e}")
        assert 'SecurityError' in str(e), f"Expected SecurityError, got: {e}"
        security_error_received = True

    assert security_error_received, \
        "Expected CSMS to respond with SecurityError CALLERROR for unauthorized message(s)"

    start_task.cancel()
