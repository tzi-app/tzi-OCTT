"""
Test case name      Reset Charging Station - With Ongoing Transaction - OnIdle
Test case Id        TC_B_21_CSMS
Use case Id(s)      B12
Requirement(s)      B12.FR.01, B12.FR.03, E07.FR.03

Requirement Details:
    B12.FR.01: The Charging Station SHALL respond with a ResetResponse(Scheduled), to indicate whether the
               Charging Station will attempt to reset itself or EVSE after all transactions on Charging
               Station or EVSE have ended.
        Precondition: When the Charging Station receives a ResetRequest(OnIdle) AND a transaction is ongoing
    B12.FR.03: The transaction of the Charging Station SHALL be terminated normally, before the reboot, e.g.
               as in E06 - Stop Transaction.
        Precondition: If no evseId is supplied AND If any transaction is in progress and an OnIdle reset is
                      received.
    E07.FR.03: (not found in OCPP 2.1 Part 2)
System under test   CSMS

Description         This test case covers how the CSMS can remotely request the Charging Station to reset
                    itself by sending a ResetRequest during a transaction. When ResetRequest "OnIdle" is send
                    the charging stations schedules a reboot after all transactions are stopped.

                    This could for example be necessary if the Charging Station is not functioning correctly.

Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP
                    specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to reboot the Charging Station with status OnIdle

1. The CSMS sends a ResetRequest
    with status OnIdle
2. The Test System responds with a ResetResponse
    with status Scheduled
3. The Test System sends a TransactionEventRequest.
    - eventType Updated
    - triggerReason StopAuthorized
    - transactionInfo.chargingState EVConnected
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
4. The CSMS responds with a TransactionEventResponse.
5. The Test System sends a TransactionEventRequest.
    - eventType Ended
    - triggerReason EVCommunicationLost
    - transactionInfo.chargingState Idle
    - transactionInfo.stoppedReason EVDisconnected
6. The CSMS responds with a TransactionEventResponse.
7. The Test System sends a BootNotificationRequest
    with reason ScheduledReset
8. The CSMS responds with a BootNotificationResponse
9. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
10. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message ResetRequest
    - type OnIdle
    - evseId must be omitted
* Step 8:
    Message BootNotificationResponse
    - status Accepted

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.5. Page 82 - (2026-04) - B12 - Reset with ongoing transaction allows wait for cable disconnection
        (Part 2 errata - applies to this test via use case B12)
        New requirements have been added to clarify the expected behavior when a reset is requested during an
        ongoing transaction, including the requirement to allow waiting for cable disconnection before
        performing the reset. Requirements were further updated for clarity.

        New requirement

        | ID | Precondition | Requirement definition | Note |
        | B12.FR.11 | B12.FR.03 AND / The transaction(s) on the EVSE(s) are terminated | The Charging Station
          MAY wait for cable disconnection before initiating a reboot | |
        | B12.FR.12 | B12.FR.07 AND / The transaction on the EVSE is terminated | The Charging Station MAY
          wait for cable disconnection before initiating a reset of the EVSE | |
        | B12.FR.13 | B12.FR.11 | The Charging Station SHALL reboot | |
        | B12.FR.14 | B12.FR.12 | The Charging Station SHALL reset the EVSE | |

        Changed requirement

        | | ID | Precondition | Requirement definition | Note |
        | Old | B12.FR.01 | When the Charging Station receives a ResetRequest(OnIdle) AND a transaction is
          ongoing | The Charging Station SHALL respond with a ResetResponse(Scheduled), [removed: to indicate
          whether the Charging Station will attempt to reset itself or EVSE after all transactions on Charging
          Station or EVSE have ended.] | |
        | New | B12.FR.01 | When the Charging Station receives a ResetRequest(OnIdle) AND a transaction is
          ongoing | The Charging Station SHALL respond with a ResetResponse(Scheduled) | |
        | Old | B12.FR.02 | When the Charging Station receives a ResetRequest(Immediate) AND a transaction is
          ongoing | The Charging Station SHALL respond with a ResetResponse(Accepted), [removed: to indicate
          whether the Charging Station will attempt to reset itself or EVSE.] | |
        | New | B12.FR.02 | When the Charging Station receives a ResetRequest(Immediate) AND a transaction is
          ongoing | The Charging Station SHALL respond with a ResetResponse(Accepted) | |

        | | ID | Precondition | Requirement definition | Note |
        | Old | B12.FR.03 | If no evseId is supplied / [removed: AND] / [removed: If any transaction is in
          progress and an OnIdle reset is received.] | The transaction of the Charging Station SHALL be
          terminated normally, before the reboot, e.g. as in E06 - Stop Transaction. | |
        | New | B12.FR.03 | B12.FR.01 AND / If no evseId is supplied | The transaction of the Charging Station
          SHALL be terminated normally, before the reboot, e.g. as in E06 - Stop Transaction. | |
        | Old | B12.FR.04 | If no evseId is supplied / [removed: AND] / [removed: If any transaction is in
          progress and an Immediate Reset is received.] | The Charging Station SHALL attempt to terminate any
          transaction in progress and send a TransactionEventRequest (eventType = Ended) message with
          triggerReason = ResetCommand and transactionInfo.stoppedReason = ImmediateReset for each terminated
          transaction before performing a reboot. | |
        | New | B12.FR.04 | B12.FR.02 AND / If no evseId is supplied | The Charging Station SHALL attempt to
          terminate any transaction in progress and send a TransactionEventRequest (eventType = Ended) message
          with triggerReason = ResetCommand and transactionInfo.stoppedReason = ImmediateReset for each
          terminated transaction before performing a reboot. | |
        | Old | B12.FR.05 | [removed: If an Immediate Reset without evseId is received and] the
          TransactionEventResponse is not received within timeout. | The Charging Station SHALL queue the
          TransactionEventRequest, reboot and resend the TransactionEventRequest after the reboot. | |
        | New | B12.FR.05 | B12.FR.04 AND / the TransactionEventResponse is not received within timeout. | The
          Charging Station SHALL queue the TransactionEventRequest, reboot and resend the
          TransactionEventRequest after the reboot. | |
        | Old | B12.FR.07 | If an evseId is supplied / [removed: AND] / [removed: If a transaction is in
          progress on the EVSE and an OnIdle reset is received.] | The transaction on the EVSE SHALL be
          terminated normally, before the reset, e.g. as in E06 - Stop Transaction. | |
        | New | B12.FR.07 | B12.FR.01 AND / If an evseId is supplied | The transaction on the EVSE SHALL be
          terminated normally, before the reset, e.g. as in E06 - Stop Transaction. | |
        | Old | B12.FR.08 | If an evseId is supplied / [removed: AND] / [removed: If a transaction is in
          progress on the EVSE and an Immediate Reset is received.] | The Charging Station SHALL attempt to
          terminate the transaction in progress on the EVSE and send a TransactionEventRequest (eventType =
          Ended) message with triggerReason = ResetCommand and transactionInfo.stoppedReason = ImmediateReset
          before resetting the EVSE. | |
        | New | B12.FR.08 | B12.FR.02 AND / If an evseId is supplied | The Charging Station SHALL attempt to
          terminate the transaction in progress on the EVSE and send a TransactionEventRequest (eventType =
          Ended) message with triggerReason = ResetCommand and transactionInfo.stoppedReason = ImmediateReset
          before resetting the EVSE. | |
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
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_21(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(
        cp, id_token=VALID_ID_TOKEN, id_token_type=VALID_ID_TOKEN_TYPE)

    # Manual Action: Request the CSMS to reboot the Charging Station with status OnIdle
    # 1. The CSMS sends a ResetRequest with status OnIdle
    # 2. The Test System responds with a ResetResponse with status Scheduled
    cp.set_response('Reset', status='Scheduled')
    reset_request = await cp.wait_for_request(
        'Reset', manual_action=reset(BASIC_AUTH_CP, 'OnIdle'))
    assert reset_request.type == 'OnIdle', \
        f"Expected ResetRequest.type OnIdle, got: {reset_request.type}"
    assert reset_request.evse_id is None, \
        f"ResetRequest.evseId must be omitted, got: {reset_request.evse_id}"

    # 3. The Test System sends a TransactionEventRequest.
    #    - eventType Updated
    #    - triggerReason StopAuthorized
    #    - transactionInfo.chargingState EVConnected
    #    - idToken.idToken <Configured valid_idtoken_idtoken>
    #    - idToken.type <Configured valid_idtoken_type>
    # 4. The CSMS responds with a TransactionEventResponse.
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='StopAuthorized',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'EVConnected'},
        id_token={'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
    ))

    # 5. The Test System sends a TransactionEventRequest.
    #    - eventType Ended
    #    - triggerReason EVCommunicationLost
    #    - transactionInfo.chargingState Idle
    #    - transactionInfo.stoppedReason EVDisconnected
    # 6. The CSMS responds with a TransactionEventResponse.
    await cp.call(call.TransactionEvent(
        event_type='Ended',
        timestamp=utc_now_iso(),
        trigger_reason='EVCommunicationLost',
        seq_no=cp.next_seq_no(),
        transaction_info={
            'transaction_id': transaction_id,
            'charging_state': 'Idle',
            'stopped_reason': 'EVDisconnected',
        },
    ))

    # 7. The Test System sends a BootNotificationRequest with reason ScheduledReset
    # 8. The CSMS responds with a BootNotificationResponse
    boot_response = await cp.send_boot_notification(reason='ScheduledReset')
    assert boot_response.status == 'Accepted', \
        f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

    # 9.  The Test System notifies the CSMS about the current state of all connectors.
    #     StatusNotificationRequest - connectorStatus Available
    #     NotifyEventRequest - trigger Delta, actualValue "Available",
    #                          component.name "Connector", variable.name "AvailabilityState"
    # 10. The CSMS responds accordingly.
    await cp.send_all_connectors_status('Available')

    start_task.cancel()
