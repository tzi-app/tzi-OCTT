"""
Test case name      Reset ImmediateAndResume - With Ongoing Transaction - Resuming Energy Transfer
Test case Id        TC_B_103_CSMS
Use case Id(s)      B13
Requirement(s)      B13.FR.31

Requirement Details:
    B13.FR.31: CSMS SHALL send the SetChargingProfileRequest for chargingProfilePurpose = TxProfile for these
               transactions again.
        Precondition: B13.FR.30 AND CSMS has a charging profile of chargingProfilePurpose = TxProfile for
                      transactions reported with triggerReason = TxResumed AND
                      SmartChargingCtrlr.ChargingProfilePersistence for instance = "TxProfile" = false or
                      absent
System under test   CSMS

Description         This test case covers how the CSMS can remotely request the Charging Station to reset
                    itself by sending a ResetRequest during a transaction. When ResetRequest "Immediate" is
                    send the charging stations will try to stop all transactions before rebooting.

                    This could for example be necessary if the Charging Station is not functioning correctly.

Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP
                    specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to reboot the Charging Station with status ImmediateAndResume

1. The CSMS sends a ResetRequest
    with status ImmediateAndResume
2. The Test System responds with a ResetResponse
    with status Accepted
3. The Test System sends a TransactionEventRequest.
    - eventType Updated
    - triggerReason ResetCommand
    - idToken is omitted
4. The CSMS responds with a TransactionEventResponse.
5. The Test System sends a BootNotificationRequest
    with reason RemoteReset
6. The CSMS responds with a BootNotificationResponse
7. The Test System notifies the CSMS about the current state of all connectors.
    For <Configured connectorId>:
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Occupied"
    - component.name "Connector"
    - variable.name "AvailabilityState"
    For <Other connector(s)>:
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
8. The CSMS responds accordingly.
9 The Test System sends a SecurityEventNotificationRequest
    with
    - type ResetOrReboot
10 The CSMS responds with a SecurityEventNotificationResponse
11. The Test System sends a TransactionEventRequest.
    - eventType Updated
    - triggerReason TxResumed
    - transactionInfo.chargingState Charging
    - idToken is omitted
12. The CSMS responds with a TransactionEventResponse.

Tool validations
* Step 1:
    Message ResetRequest
    - type ImmediateAndResume
* Step 6:
    Message BootNotificationResponse
    - status Accepted

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from trigger import reset
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_103(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(
        cp, evse_id=CONFIGURED_EVSE_ID, connector_id=CONFIGURED_CONNECTOR_ID)

    # Manual Action: Request the CSMS to reboot the Charging Station with status
    #                ImmediateAndResume
    # 1. The CSMS sends a ResetRequest with status ImmediateAndResume
    # 2. The Test System responds with a ResetResponse with status Accepted
    reset_request = await cp.wait_for_request(
        'Reset', manual_action=reset(BASIC_AUTH_CP, 'ImmediateAndResume'))
    assert reset_request.type == 'ImmediateAndResume', \
        f"Expected ResetRequest.type ImmediateAndResume, got: {reset_request.type}"

    # 3. The Test System sends a TransactionEventRequest.
    #    - eventType Updated
    #    - triggerReason ResetCommand
    #    - idToken is omitted
    # 4. The CSMS responds with a TransactionEventResponse.
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='ResetCommand',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
    ))

    # 5. The Test System sends a BootNotificationRequest with reason RemoteReset
    # 6. The CSMS responds with a BootNotificationResponse
    boot_response = await cp.send_boot_notification(reason='RemoteReset')
    assert boot_response.status == 'Accepted', \
        f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

    # 7. The Test System notifies the CSMS about the current state of all connectors, each
    #    with a NotifyEventRequest (trigger Delta, component.name "Connector", variable.name
    #    "AvailabilityState"):
    #    For <Configured connectorId>: actualValue "Occupied"
    #    For <Other connector(s)>: actualValue "Available"
    # 8. The CSMS responds accordingly.
    await cp.send_all_connectors_status(
        'Available', other_status={CONFIGURED_EVSE_ID: 'Occupied'}, status_notification=False)

    # 9.  The Test System sends a SecurityEventNotificationRequest with type ResetOrReboot
    # 10. The CSMS responds with a SecurityEventNotificationResponse
    await cp.send_security_event_notification('ResetOrReboot')

    # 11. The Test System sends a TransactionEventRequest.
    #     - eventType Updated
    #     - triggerReason TxResumed
    #     - transactionInfo.chargingState Charging
    #     - idToken is omitted
    # 12. The CSMS responds with a TransactionEventResponse.
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='TxResumed',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'Charging'},
    ))

    start_task.cancel()
