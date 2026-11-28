"""
Test case name      Reset ImmediateAndResume - With Ongoing Transaction and SmartCharging - resuming
                    energytransfer
Test case Id        TC_B_116_CSMS
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
                    sent the charging stations will try to stop all transactions before rebooting.

                    This could for example be necessary if the Charging Station is not functioning correctly.

Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP
                    specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual action: trigger CSMS to set a Charging Profile of type TxProfile on <transactionId>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with status Accepted

Manual Action: Request the CSMS to reboot the Charging Station with status ImmediateAndResume

3. The CSMS sends a ResetRequest
4. The Test System responds with a ResetResponse with status Accepted
5. The Test System sends a TransactionEventRequest.
    - eventType Updated
    - triggerReason ResetCommand
6. The CSMS responds with a TransactionEventResponse.
7. The Test System sends a BootNotificationRequest with reason RemoteReset
8. The CSMS responds with a BootNotificationResponse
9. The Test System notifies the CSMS about the current state of all connectors.
    For <Configured connectorId>:
    Message: StatusNotificationRequest
    - connectorStatus Occupied
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Occupied"
    - component.name "Connector"
    - variable.name "AvailabilityState"
    For <Other connector(s)>:
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
10. The CSMS responds accordingly.
11. The Test System sends a TransactionEventRequest.
    - eventType Updated
    - triggerReason TxResumed
    - idToken is omitted
12. The CSMS responds with a TransactionEventResponse.
13. The CSMS sends a SetChargingProfileRequest
14. The Test System responds with a SetChargingProfileResponse with status Accepted

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose TxProfile
* Step 3:
    Message ResetRequest
    - type ImmediateAndResume
* Step 8:
    Message BootNotificationResponse
    - status Accepted
* Step 13:
    Message: SetChargingProfileRequest must either contain an identical chargingProfile as in Step 1 or
             identical from the time of step 11 onwards.

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.7. Page 1007/1008 - (2026-02) - TC_B_116_CSMS -
        Added SecurityEventNotificationRequest steps and updated tool validations.

        | Test case name | Reset ImmediateAndResume - With Ongoing Transaction and SmartCharging - resuming
          energytransfer |
        | Test case Id | TC_B_116_CSMS |
        | … | |
        | Description | This test case covers how the CSMS can remotely request the Charging Station to reset
          itself by sending a ResetRequest during a transaction. When ResetRequest [removed: "Immediate"]
          "ImmediateAndResume" is sent the charging stations will try to stop all transactions before
          rebooting. |

        | Main / (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | 9. The Test System notifies the CSMS about the current state of all connectors. / For <Configured
          connectorId>: / [removed: Message: StatusNotificationRequest] / [removed: - connectorStatus
          Occupied] / Message: NotifyEventRequest / - trigger Delta / - actualValue "Occupied" / -
          component.name "Connector" / - variable.name "AvailabilityState" /  / For <Other connector(s)>: /
          [removed: Message: StatusNotificationRequest] / [removed: - connectorStatus Available] / Message:
          NotifyEventRequest / - trigger Delta / - actualValue "Available" / - component.name "Connector" / -
          variable.name "AvailabilityState" | 10. The CSMS responds accordingly. |

        | Main / (Test scenario) | |
        | 11. The Test System sends a SecurityEventNotificationRequest with / - type ResetOrReboot | 12. The
          CSMS responds with a SecurityEventNotificationResponse |
        | [removed: 11.] 13. The Test System sends a TransactionEventRequest. / - eventType Updated / -
          triggerReason TxResumed / - idToken is omitted | [removed: 12.] 14. The CSMS responds with a
          TransactionEventResponse. |
        | [removed: 14.] 16. The Test System responds with a SetChargingProfileResponse / with status Accepted
          | [removed: 13.] 15. The CSMS sends a SetChargingProfileRequest |

        | Tool validations |
        | * Step 1: / … * Step [removed: 13] 15: / [removed: Message: SetChargingProfileRequest must either
          contain an identical chargingProfile as in Step 1 or identical from the time of step 11 onwards.] /
          Message: SetChargingProfileRequest / - chargingProfile.chargingProfilePurpose TxProfile |
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from trigger import reset, send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_116(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(
        cp, evse_id=CONFIGURED_EVSE_ID, connector_id=CONFIGURED_CONNECTOR_ID)

    # Manual action: trigger CSMS to set a Charging Profile of type TxProfile on <transactionId>
    # 1. The CSMS sends a SetChargingProfileRequest
    # 2. The Test System responds with a SetChargingProfileResponse with status Accepted
    set_charging_profile = await cp.wait_for_request(
        'SetChargingProfile',
        manual_action=send_call(BASIC_AUTH_CP, 'SetChargingProfile', {
            'evseId': CONFIGURED_EVSE_ID,
            'chargingProfile': {
                'id': 1,
                'stackLevel': 0,
                'chargingProfilePurpose': 'TxProfile',
                'chargingProfileKind': 'Relative',
                'transactionId': transaction_id,
                'chargingSchedule': [{
                    'id': 1,
                    'chargingRateUnit': 'A',
                    'chargingSchedulePeriod': [{'startPeriod': 0, 'limit': 16.0}],
                }],
            },
        }))
    assert set_charging_profile.charging_profile.charging_profile_purpose == 'TxProfile', \
        f"Expected chargingProfilePurpose TxProfile, got: " \
        f"{set_charging_profile.charging_profile.charging_profile_purpose}"

    # Manual Action: Request the CSMS to reboot the Charging Station with status
    #                ImmediateAndResume
    # 3. The CSMS sends a ResetRequest
    # 4. The Test System responds with a ResetResponse with status Accepted
    reset_request = await cp.wait_for_request(
        'Reset', manual_action=reset(BASIC_AUTH_CP, 'ImmediateAndResume'))
    assert reset_request.type == 'ImmediateAndResume', \
        f"Expected ResetRequest.type ImmediateAndResume, got: {reset_request.type}"

    # 5. The Test System sends a TransactionEventRequest.
    #    - eventType Updated
    #    - triggerReason ResetCommand
    # 6. The CSMS responds with a TransactionEventResponse.
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='ResetCommand',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
    ))

    # 7. The Test System sends a BootNotificationRequest with reason RemoteReset
    # 8. The CSMS responds with a BootNotificationResponse
    boot_response = await cp.send_boot_notification(reason='RemoteReset')
    assert boot_response.status == 'Accepted', \
        f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

    # 9.  The Test System notifies the CSMS about the current state of all connectors, each
    #     with a NotifyEventRequest (trigger Delta, component.name "Connector", variable.name
    #     "AvailabilityState"). Errata 2026-09 (6.3.7) removed the StatusNotificationRequests.
    #     For <Configured connectorId>: actualValue "Occupied"
    #     For <Other connector(s)>: actualValue "Available"
    # 10. The CSMS responds accordingly.
    await cp.send_all_connectors_status(
        'Available', other_status={CONFIGURED_EVSE_ID: 'Occupied'}, status_notification=False)

    # Errata 2026-09 (6.3.7), new steps 11-12:
    # 11. The Test System sends a SecurityEventNotificationRequest with type ResetOrReboot
    # 12. The CSMS responds with a SecurityEventNotificationResponse
    await cp.send_security_event_notification('ResetOrReboot')

    # 13. The Test System sends a TransactionEventRequest.
    #     - eventType Updated
    #     - triggerReason TxResumed
    #     - idToken is omitted
    # 14. The CSMS responds with a TransactionEventResponse.
    # Only a SetChargingProfileRequest that follows the TxResumed event is the one of step 15.
    cp.forget_requests('SetChargingProfile')
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='TxResumed',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
    ))

    # 15. The CSMS sends a SetChargingProfileRequest: the TxProfile of the resumed
    #     transaction again (B13.FR.31)
    # 16. The Test System responds with a SetChargingProfileResponse with status Accepted
    set_charging_profile = await cp.wait_for_request('SetChargingProfile')
    assert set_charging_profile.charging_profile.charging_profile_purpose == 'TxProfile', \
        f"Expected chargingProfilePurpose TxProfile, got: " \
        f"{set_charging_profile.charging_profile.charging_profile_purpose}"

    start_task.cancel()
