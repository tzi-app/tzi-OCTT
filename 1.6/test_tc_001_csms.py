"""
Test case name      Cold Boot Charge Point
Test case Id        TC_001_CSMS
OCPP Version        1.6
Chapter             3.1 - Cold Boot Charge Point
Section             3.1.1
System under test   Central System
PDF Reference       CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, Page 2 (of 73), Table 122
Doc Reference       CompliancyTestTool-TestCaseDocument.html, Page 110/176, Table 122

Description         This scenario is used to startup the Charge Point and let it register itself
                    at the Central System.

Purpose             To test if the Central System is able to handle a boot process.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Scenario Detail(s)
    Charge Point (Tool)                              Central System (SUT)
    ─────────────────────────────────────────────────────────────────────────────
    1. The Charge Point sends a                       2. The Central System responds with a
       BootNotification.req                              BootNotification.conf

    [Send a StatusNotification per connector
     and connectorId=0.]
    3. The Charge Point sends a                       4. The Central System responds with a
       StatusNotification.req                            StatusNotification.conf

    [Every x seconds.]
    5. The Charge Point sends a                       6. The Central System responds with a
       Heartbeat.req                                     Heartbeat.conf

Tool Validations
    Charge Point (Tool):
        * Step 1:
          (Message: BootNotification.req)
        * Step 3:
          (Message: StatusNotification.req)
          - status is Available
          NOTE: The doc says "per connector and connectorId=0" but does not specify
          the total number of connectors. Test assumes a single-connector CP
          (connectorId=0 for the main controller + connectorId=1).
        * Step 5:
          (Message: Heartbeat.req)
          Send a Heartbeat.req every x seconds. x equals interval from step 2.
          NOTE: The test sends a single heartbeat immediately (without waiting
          interval seconds) since we are validating the CSMS response, not the
          CP's heartbeat scheduling.

    Central System (SUT):
        * Step 2:
          (Message: BootNotification.conf)
          - The status is Accepted

Expected Result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): n/a

OCPP 1.6 Messages Used:
    - BootNotification.req / BootNotification.conf
    - StatusNotification.req / StatusNotification.conf
    - Heartbeat.req / Heartbeat.conf

Key Fields (supplementary - from OCPP 1.6 spec, not from test case document):
    BootNotification.req:
        - chargePointVendor (String, required, max 20 chars)
        - chargePointModel (String, required, max 20 chars)
        - chargePointSerialNumber (String, optional, max 25 chars)
        - chargeBoxSerialNumber (String, optional, max 25 chars)
        - firmwareVersion (String, optional, max 50 chars)
        - iccid (String, optional, max 20 chars)
        - imsi (String, optional, max 20 chars)
        - meterType (String, optional, max 25 chars)
        - meterSerialNumber (String, optional, max 25 chars)

    BootNotification.conf:
        - status (RegistrationStatus: Accepted | Pending | Rejected)
        - currentTime (dateTime, required)
        - interval (Integer, required - heartbeat interval in seconds)

    StatusNotification.req:
        - connectorId (Integer, required, >= 0; 0 = Charge Point main controller)
        - errorCode (ChargePointErrorCode, required)
        - status (ChargePointStatus: Available | Preparing | Charging | SuspendedEVSE |
                  SuspendedEV | Finishing | Reserved | Unavailable | Faulted)
        - timestamp (dateTime, optional)

    StatusNotification.conf:
        - (empty payload)

    Heartbeat.req:
        - (empty payload)

    Heartbeat.conf:
        - currentTime (dateTime, required)
"""

import asyncio
import os
import pytest

from ocpp.v16.enums import RegistrationStatus

from charge_point import TziChargePoint16
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_001(connection):
    # Step 0: Verify WebSocket connection was established
    assert connection.open

    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Send BootNotification.req, expect Accepted
    boot_response = await cp.send_boot_notification()
    assert boot_response is not None
    assert boot_response.status == RegistrationStatus.accepted
    assert boot_response.current_time is not None
    assert boot_response.interval is not None
    assert boot_response.interval > 0

    # Step 3-4: Send StatusNotification.req per connector (connectorId=0 and connectorId=1)
    #           with status=Available
    for connector_id in (0, 1):
        status_response = await cp.send_status_notification(connector_id)
        assert status_response is not None

    # Step 5-6: Send Heartbeat.req, expect currentTime in response
    heartbeat_response = await cp.send_heartbeat()
    assert heartbeat_response is not None
    assert heartbeat_response.current_time is not None

    start_task.cancel()
