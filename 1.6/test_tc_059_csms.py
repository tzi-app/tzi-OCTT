"""
Test case name      Remote Start Transaction with Charging Profile
Test case Id        TC_059_CSMS
Feature profile     SmartCharging
Document ref        Table 182, Section 3.19.4, Pages 156-157/176 (Section 3 PDF pp. 53-54)

Description         The Central System starts a transaction on a Charge Point with a ChargingProfile.
Purpose             To check whether the Central System can trigger a Charge Point to start a transaction with a
                    Charging Profile.
Prerequisite(s)     The Central System supports the Smart Charging feature profile.

Before State:
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
    1.  The Central System sends a RemoteStartTransaction.req to the Charge Point.
    2.  The Charge Point responds with a RemoteStartTransaction.conf.
    3.  The Charge Point sends an Authorize.req to the Central System.
    4.  The Central System responds with an Authorize.conf.
        [The charging cable is plugged in]
    5.  The Charge Point sends a StatusNotification.req to the Central System.
    6.  The Central System responds with a StatusNotification.conf.
    7.  The Charge Point sends a StartTransaction.req to the Central System.
    8.  The Central System responds with a StartTransaction.conf.
    9.  The Charge Point sends a StatusNotification.req to the Central System.
    10. The Central System responds with a StatusNotification.conf.

Tool validations
    * Step 1:
        (Message: RemoteStartTransaction.req)
        - idTag is <Configured valid IdTag>
        - connectorId is <Configured ConnectorId>
        - chargingProfile.chargingProfilePurpose is TxProfile
        - chargingProfile.transactionId is omitted
        - The first chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod is 0
        - csChargingProfiles.recurrencyKind is <Omitted>
        AND
        - csChargingProfiles.chargingProfileKind is Absolute or Relative
        AND
          if csChargingProfiles.chargingProfileKind is Absolute:
            - csChargingProfiles.validFrom <Not omitted> AND
            - csChargingProfiles.validTo <Not omitted> AND
            - csChargingProfiles.chargingSchedule.startSchedule <Not omitted> AND
            - csChargingProfiles.chargingSchedule.duration <Not omitted>
          if csChargingProfiles.chargingProfileKind is Relative:
            - csChargingProfiles.chargingSchedule.startSchedule <Omitted>

    * Step 2:
        (Message: RemoteStartTransaction.conf)
        - status is Accepted

    * Step 3:
        (Message: Authorize.req)
        - idTag is the idTag from step 1.

    * Step 4:
        (Message: Authorize.conf)
        - idTagInfo.status is Accepted

    * Step 5:
        (Message: StatusNotification.req)
        - status is Preparing
        - connectorId is the connectorId from step 1.

    * Step 6:
        (Message: StatusNotification.conf)
        - Response acknowledged

    * Step 7:
        (Message: StartTransaction.req)
        - idTag is the idTag from step 1.
        - connectorId is the connectorId from step 1.

    * Step 8:
        (Message: StartTransaction.conf)
        - status is Accepted

    * Step 9:
        (Message: StatusNotification.req)
        - status is Charging
        - connectorId is the connectorId from step 1.

    * Step 10:
        (Message: StatusNotification.conf)
        - Response acknowledged

Expected result(s):
    CP (Tool): n/a
    CS (SUT): The Central System has started a transaction on the Charge Point and accepts
    the transaction that is started on the Charge Point.

NOTE: Step 6 and Step 10 (StatusNotification.conf) have no explicit tool validations in the
official document - "Response acknowledged" is inferred.
NOTE: "csChargingProfiles" in the tool validations appears to be the document's alias for the
chargingProfile field in the RemoteStartTransaction.req - to be confirmed.
"""

import asyncio
import os
from datetime import datetime, timedelta
import pytest

from ocpp.v16.enums import AuthorizationStatus, ChargePointStatus

from charge_point import TziChargePoint16
from trigger import trigger_v16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
ACTION_TIMEOUT = int(os.environ.get('CSMS_ACTION_TIMEOUT', '30'))
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))
VALID_ID_TAG = os.environ.get('VALID_ID_TOKEN', 'TEST_TAG')


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_059(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Wait for CSMS to send RemoteStartTransaction.req with charging profile
    asyncio.create_task(trigger_v16(BASIC_AUTH_CP, 'remote-start-transaction', {
        'idTag': VALID_ID_TAG,
        'connectorId': CONNECTOR_ID,
        'chargingProfile': {
            'chargingProfileId': 1,
            'stackLevel': 0,
            'chargingProfilePurpose': 'TxProfile',
            'chargingProfileKind': 'Absolute',
            'validFrom': datetime.now().isoformat() + 'Z',
            'validTo': (datetime.now() + timedelta(days=1)).isoformat() + 'Z',
            'chargingSchedule': {
                'startSchedule': datetime.now().isoformat() + 'Z',
                'chargingRateUnit': 'A',
                'duration': 86400,
                'chargingSchedulePeriod': [
                    {'startPeriod': 0, 'limit': 6.0, 'numberPhases': 3},
                ],
            },
        },
    }))
    await asyncio.wait_for(cp._received_remote_start.wait(), timeout=ACTION_TIMEOUT)
    id_tag = cp._remote_start_id_tag
    assert id_tag is not None
    assert cp._remote_start_connector_id == CONNECTOR_ID

    # Validate charging profile fields
    profile = cp._remote_start_charging_profile
    assert profile is not None
    assert profile['charging_profile_purpose'] == 'TxProfile'
    assert profile.get('transaction_id') is None  # must be omitted
    assert profile.get('recurrency_kind') is None  # must be omitted

    kind = profile['charging_profile_kind']
    assert kind in ('Absolute', 'Relative')

    schedule = profile['charging_schedule']
    periods = schedule['charging_schedule_period']
    assert len(periods) > 0
    assert periods[0]['start_period'] == 0

    if kind == 'Absolute':
        assert profile.get('valid_from') is not None
        assert profile.get('valid_to') is not None
        assert schedule.get('start_schedule') is not None
        assert schedule.get('duration') is not None
    elif kind == 'Relative':
        assert schedule.get('start_schedule') is None

    # Step 3-4: Authorize with the idTag from remote start
    auth_response = await cp.send_authorize(id_tag)
    assert auth_response.id_tag_info['status'] == AuthorizationStatus.accepted

    # Step 5-6: StatusNotification(Preparing)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.preparing)

    # Step 7-8: StartTransaction
    start_response = await cp.send_start_transaction(CONNECTOR_ID, id_tag)
    assert start_response.id_tag_info['status'] == AuthorizationStatus.accepted

    # Step 9-10: StatusNotification(Charging)
    await cp.send_status_notification(CONNECTOR_ID, status=ChargePointStatus.charging)

    start_task.cancel()
