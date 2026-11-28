"""
Test case name      Set Charging Profile - Resuming transaction after interruption - TxResumptionTimeout not
                    expired - TxAllowEnergyTransferResumption is true
Test case Id        TC_E_117_CSMS
Use case Id(s)      E17
Requirement(s)      E17.FR.15

Requirement Details:
    E17.FR.15: CSMS SHALL send the SetChargingProfileRequest for chargingProfilePurpose = TxProfile for these
               transactions again.
        Precondition: E17.FR.14 AND CSMS has a charging profile of chargingProfilePurpose = TxProfile for
                      transactions reported with triggerReason = TxResumed AND
                      SmartChargingCtrlr.ChargingProfilePersistence for instance = "TxProfile" = false or
                      absent
        Note: The charging profiles are identical to those sent at start of transaction, since start time of
              the resumed transaction has not changed.
System under test   CSMS

Description         CSMS restores TxProfile after Charging Station resumes transactions which had a Charging
                    profile with purpose TxProfile configured.

Purpose             To verify the CSMS restores the charging profile for a transaction after resuming
                    transactions by the Charging Station.

Prerequisite(s)     N/a

Configuration State SmartChargingCtrlr.ChargingProfilePersistence is <absent>

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual Action: trigger CSMS to set a Charging Profile of type TxProfile on <transactionId>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with status Accepted

The Test System disconnects the connection.
The Test System waits the <Configured transaction duration>
The Test System restores the connection.

3. The Test System sends a BootNotificationRequest
4. The CSMS responds with a BootNotificationResponse
5. The Test System notifies the CSMS about the current state of all connectors.
    Message: NotifyEventRequest
    - eventData[0].trigger Delta
    - eventData[0].component.name "Connector"
    - eventData[0].variable.name "AvailabilityState"
    Configured EVSE.Connector:
    - eventData[0].actualValue "Occupied"
    Other connectors:
    - eventData[0].actualValue "Available"
6. The CSMS responds accordingly.
7 The Test System sends a SecurityEventNotificationRequest
    - type must be StartupOfTheDevice OR ResetOrReboot
8 The CSMS responds with a SecurityEventNotificationResponse
9 The Test System sends a NotifyEventRequest
    - eventData.trigger = Delta
    - eventData.transactionId = <transactionId from this transaction>
    - eventData.eventNotificationType = HardWiredNotification
    - eventData.severity = 3
    - eventData.actualValue = true
    - eventData.component.name = ElectricalFeed
    - eventData.variable.name = Problem
10 The CSMS responds with a NotifyEventResponse
11 The Test System sends a NotifyEventRequest
    Same content as step 9, but with actualValue = false:
    - eventData.actualValue = false
12 The CSMS responds with a NotifyEventResponse
13. The Test System sends a TransactionEventRequest
    - eventType Updated
    - triggerReason TxResumed
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.chargingState Charging
14. The CSMS responds with a TransactionEventResponse
15. The CSMS sends a SetChargingProfileRequest
16. The Test System responds with a SetChargingProfileResponse with status Accepted

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose must be TxProfile
* Step 4:
    Message: BootNotificationResponse
    - status must be Accepted
* Step 15:
    Message: SetChargingProfileRequest must contain an identical chargingProfile as in Step 1 or identical as
             of time of Step 15.

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.4. Page 1100/1101 - (2026-02) - TC_E_117_CSMS - Updated prerequisites and SetChargingProfileRequest
        tool validations
        The configuration SmartChargingCtrlr.ChargingProfilePersistence is <absent> was moved to Prerequisites
        and SetChargingProfileRequest tool validations were updated.

        | Test case name | Set Charging Profile - Resuming transaction after interruption -
          TxResumptionTimeout not expired - TxAllowEnergyTransferResumption is true |
        | Test case Id | TC_E_117_CSMS |
        | … | |
        | Prerequisite(s) | SmartChargingCtrlr.ChargingProfilePersistence is <absent> /
          TxCtrlr.TxResumptionTimeout is 999 / TxCtrlr.TxAllowEnergyTransferResumption is true |

        | Before (Preparations) |
        | Configuration State: / [removed: SmartChargingCtrlr.ChargingProfilePersistence is <absent>] / N/a |
        | … |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | 7. The Test System sends a SecurityEventNotificationRequest / - type must be [removed:
          StartupOfTheDevice OR] ResetOrReboot | 8. The CSMS responds with a SecurityEventNotificationResponse
          |
        | … | |

        | Tool validations |
        | … / * Step 15: / [removed: Message: SetChargingProfileRequest must contain an identical
          chargingProfile as in Step 1 or identical as of time of Step 15.] / Message:
          SetChargingProfileRequest / - chargingProfile.chargingProfilePurpose must be TxProfile |
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_117(connection, reconnect):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites (errata 2026-09, 6.3.4): SmartChargingCtrlr.ChargingProfilePersistence is
    # <absent>, TxCtrlr.TxResumptionTimeout is 999, TxCtrlr.TxAllowEnergyTransferResumption is true
    cp.variables = {
        'TxCtrlr.TxResumptionTimeout': '999',
        'TxCtrlr.TxAllowEnergyTransferResumption': 'true',
    }
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Reusable State: State is EnergyTransferStarted
    transaction_id = await energy_transfer_started(cp)

    # Manual Action: trigger CSMS to set a Charging Profile of type TxProfile on <transactionId>
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

    # The Test System disconnects the connection.
    await cp.disconnect()
    # The Test System waits the <Configured transaction duration>
    await asyncio.sleep(TRANSACTION_DURATION)
    # The Test System restores the connection.
    start_task = cp.use_connection(await reconnect(
        BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD)))

    # 3. The Test System sends a BootNotificationRequest
    # 4. The CSMS responds with a BootNotificationResponse
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == 'Accepted', \
        f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

    # 5. The Test System notifies the CSMS about the current state of all connectors.
    #    Message: NotifyEventRequest
    #    - eventData[0].trigger Delta
    #    - eventData[0].component.name "Connector"
    #    - eventData[0].variable.name "AvailabilityState"
    #    Configured EVSE.Connector: eventData[0].actualValue "Occupied"
    #    Other connectors: eventData[0].actualValue "Available"
    # 6. The CSMS responds accordingly.
    await cp.send_all_connectors_status(
        'Available', other_status={CONFIGURED_EVSE_ID: 'Occupied'}, status_notification=False)

    # 7. The Test System sends a SecurityEventNotificationRequest
    #    - type must be ResetOrReboot (errata 2026-09, 6.3.4)
    # 8. The CSMS responds with a SecurityEventNotificationResponse
    await cp.send_security_event_notification('ResetOrReboot')

    # 9. The Test System sends a NotifyEventRequest
    #    - eventData.trigger = Delta
    #    - eventData.transactionId = <transactionId from this transaction>
    #    - eventData.eventNotificationType = HardWiredNotification
    #    - eventData.severity = 3
    #    - eventData.actualValue = true
    #    - eventData.component.name = ElectricalFeed
    #    - eventData.variable.name = Problem
    # 10. The CSMS responds with a NotifyEventResponse
    await cp.send_event('ElectricalFeed', 'Problem', 'true', transaction_id=transaction_id, severity=3)

    # 11. The Test System sends a NotifyEventRequest
    #     Same content as step 9, but with actualValue = false:
    #     - eventData.actualValue = false
    # 12. The CSMS responds with a NotifyEventResponse
    await cp.send_event('ElectricalFeed', 'Problem', 'false', transaction_id=transaction_id, severity=3)

    # 13. The Test System sends a TransactionEventRequest
    #     - eventType Updated
    #     - triggerReason TxResumed
    #     - transactionInfo.transactionId <transactionId>
    #     - transactionInfo.chargingState Charging
    # 14. The CSMS responds with a TransactionEventResponse
    # Only a SetChargingProfileRequest that follows the TxResumed event is the one of step 15.
    cp.forget_requests('SetChargingProfile')
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='TxResumed',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'Charging'},
    ))

    # 15. The CSMS sends a SetChargingProfileRequest
    # 16. The Test System responds with a SetChargingProfileResponse with status Accepted
    set_charging_profile = await cp.wait_for_request('SetChargingProfile')
    assert set_charging_profile.charging_profile.charging_profile_purpose == 'TxProfile', \
        f"Expected chargingProfilePurpose TxProfile, got: " \
        f"{set_charging_profile.charging_profile.charging_profile_purpose}"

    start_task.cancel()
