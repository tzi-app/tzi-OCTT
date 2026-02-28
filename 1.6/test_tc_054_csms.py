"""
Test case name      Trigger Message
Test case Id        TC_054_CSMS
Feature profile     Remote Trigger
Document ref        OCPP 1.6 CSMS Test Cases Section 3 (CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf)
                    Table 176, pages 149-150, Section 3.18.1

Description         The Central System triggers a message from the Charge Point.

Purpose             Check whether the Central System is able to trigger a message from the Charge Point.

Prerequisite(s)     The Central System supports the Remote Trigger feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
1.  The Central System sends a TriggerMessage.req with:
        - requestedMessage = MeterValues
        - connectorId = <Configured ConnectorId>
2.  The Charge Point responds with a TriggerMessage.conf with:
        - status = Accepted
3.  The Charge Point sends a MeterValues.req
4.  The Central System responds with a MeterValues.conf

5.  The Central System sends a TriggerMessage.req with:
        - requestedMessage = Heartbeat
6.  The Charge Point responds with a TriggerMessage.conf with:
        - status = Accepted
7.  The Charge Point sends a Heartbeat.req
8.  The Central System responds with a Heartbeat.conf

9.  The Central System sends a TriggerMessage.req with:
        - requestedMessage = StatusNotification
        - connectorId = <Configured ConnectorId>
10. The Charge Point responds with a TriggerMessage.conf with:
        - status = Accepted
11. The Charge Point sends a StatusNotification.req
12. The Central System responds with a StatusNotification.conf

13. The Central System sends a TriggerMessage.req with:
        - requestedMessage = DiagnosticsStatusNotification
14. The Charge Point responds with a TriggerMessage.conf with:
        - status = Accepted
15. The Charge Point sends a DiagnosticsStatusNotification.req with:
        - status = Idle
16. The Central System responds with a DiagnosticsStatusNotification.conf

17. The Central System sends a TriggerMessage.req with:
        - requestedMessage = FirmwareStatusNotification
18. The Charge Point responds with a TriggerMessage.conf with:
        - status = Accepted OR NotImplemented
    [The following message will be sent if implemented.]
19. The Charge Point sends a FirmwareStatusNotification.req with:
        - status = Idle
20. The Central System responds with a FirmwareStatusNotification.conf

Tool validations
* Step 1:
    (Message: TriggerMessage.req)
    - requestedMessage should be MeterValues
    - connectorId should be <Configured ConnectorId>
* Step 2:
    (Message: TriggerMessage.conf)
    - status is Accepted
* Step 5:
    (Message: TriggerMessage.req)
    - requestedMessage should be Heartbeat
* Step 6:
    (Message: TriggerMessage.conf)
    - status is Accepted
* Step 9:
    (Message: TriggerMessage.req)
    - requestedMessage should be StatusNotification
    - connectorId should be <Configured ConnectorId>
* Step 10:
    (Message: TriggerMessage.conf)
    - status is Accepted
* Step 13:
    (Message: TriggerMessage.req)
    - requestedMessage should be DiagnosticsStatusNotification
* Step 14:
    (Message: TriggerMessage.conf)
    - status is Accepted
* Step 15:
    (Message: DiagnosticsStatusNotification.req)
    - status is Idle
* Step 17:
    (Message: TriggerMessage.req)
    - requestedMessage should be FirmwareStatusNotification
* Step 18:
    (Message: TriggerMessage.conf)
    - status is Accepted OR NotImplemented
* Step 19:
    (Message: FirmwareStatusNotification.req)
    - status is Idle

Expected result(s)
    The Central System can request a message from a Charge Point and receive the requested message.

Note(s)
    - Step 18 allows NotImplemented response for FirmwareStatusNotification, making steps 19-20
      conditional. This test always responds Accepted and sends the FirmwareStatusNotification
      (happy path). The NotImplemented branch (where steps 19-20 are skipped) is not exercised.
      The spec does not clarify whether the CSMS test must cover both branches.
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import DiagnosticsStatus, FirmwareStatus

from charge_point import TziChargePoint16
from trigger import trigger_v16
from utils import get_basic_auth_headers, now_iso

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_054(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # --- Cycle 1: MeterValues ---
    # Step 1-2: Wait for TriggerMessage(MeterValues, connectorId=CONNECTOR_ID)
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'trigger-message', {'requestedMessage': 'MeterValues', 'connectorId': CONNECTOR_ID}))
    await asyncio.wait_for(cp._received_trigger_message.wait(), timeout=ACTION_TIMEOUT)
    assert cp._trigger_message_requested == 'MeterValues'
    assert cp._trigger_message_connector_id == CONNECTOR_ID
    cp._received_trigger_message.clear()

    # Step 3-4: CP sends MeterValues.req
    await cp.send_meter_values(
        CONNECTOR_ID,
        [{'timestamp': now_iso(), 'sampled_value': [{'value': '0'}]}],
    )

    # --- Cycle 2: Heartbeat ---
    # Step 5-6: Wait for TriggerMessage(Heartbeat)
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'trigger-message', {'requestedMessage': 'Heartbeat'}))
    await asyncio.wait_for(cp._received_trigger_message.wait(), timeout=ACTION_TIMEOUT)
    assert cp._trigger_message_requested == 'Heartbeat'
    cp._received_trigger_message.clear()

    # Step 7-8: CP sends Heartbeat.req
    await cp.send_heartbeat()

    # --- Cycle 3: StatusNotification ---
    # Step 9-10: Wait for TriggerMessage(StatusNotification, connectorId=CONNECTOR_ID)
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'trigger-message', {'requestedMessage': 'StatusNotification', 'connectorId': CONNECTOR_ID}))
    await asyncio.wait_for(cp._received_trigger_message.wait(), timeout=ACTION_TIMEOUT)
    assert cp._trigger_message_requested == 'StatusNotification'
    assert cp._trigger_message_connector_id == CONNECTOR_ID
    cp._received_trigger_message.clear()

    # Step 11-12: CP sends StatusNotification.req
    await cp.send_status_notification(CONNECTOR_ID)

    # --- Cycle 4: DiagnosticsStatusNotification ---
    # Step 13-14: Wait for TriggerMessage(DiagnosticsStatusNotification)
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'trigger-message', {'requestedMessage': 'DiagnosticsStatusNotification'}))
    await asyncio.wait_for(cp._received_trigger_message.wait(), timeout=ACTION_TIMEOUT)
    assert cp._trigger_message_requested == 'DiagnosticsStatusNotification'
    cp._received_trigger_message.clear()

    # Step 15-16: CP sends DiagnosticsStatusNotification(Idle)
    await cp.send_diagnostics_status_notification(DiagnosticsStatus.idle)

    # --- Cycle 5: FirmwareStatusNotification ---
    # Step 17-18: Wait for TriggerMessage(FirmwareStatusNotification)
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'trigger-message', {'requestedMessage': 'FirmwareStatusNotification'}))
    await asyncio.wait_for(cp._received_trigger_message.wait(), timeout=ACTION_TIMEOUT)
    assert cp._trigger_message_requested == 'FirmwareStatusNotification'
    cp._received_trigger_message.clear()

    # Step 19-20: CP sends FirmwareStatusNotification(Idle)
    await cp.send_firmware_status_notification(FirmwareStatus.idle)

    start_task.cancel()
