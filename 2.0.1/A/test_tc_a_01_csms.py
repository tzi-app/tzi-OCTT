"""
Test case name      Basic Authentication - Valid username/password combination
Test case Id        TC_A_01_CSMS
Use case Id(s)      A00, B01
Requirement(s)      A00.FR.204, B01.FR.02

Requirement Details:
    A00.FR.204: When the Charging Station receives a BootNotificationRequest, the CSMS SHALL respond with a BootNotificationResponse.
        Precondition: A00.FR.203
    B01.FR.02: The CSMS has received BootNotificationRequest from the Charging Station. The CSMS SHALL respond to indicate whether it will accept the Charging Station.
        Precondition: B01.FR.01 The CSMS has received BootNotificationRequest from the Charging Station.
System under test   CSMS

Description         The Charging Station uses Basic authentication to authenticate itself to the CSMS, when using security
                    profile 1 or 2.
Purpose             To verify whether the CSMS is able to validate the (valid) Basic authentication credentials provided by the
                    Charging Station at the connection request.

Prerequisite(s)     The CSMS supports security profile 1 and/or 2

Test Scenario
1. The OCTT sends a HTTP upgrade request with an Authorization header, containing a username/password combination.
2. The CSMS validates the username/password combination AND upgrades the connection to a (secured) WebSocket connection.
3. The OCTT sends a BootNotificationRequest
4. The CSMS responds with a BootNotificationResponse
5. The OCTT notifies the CSMS about the current state of all connectors.
6. The CSMS responds accordingly.
"""

import asyncio
import pytest
import os

from ocpp.v201.enums import RegistrationStatusEnumType, ConnectorStatusEnumType

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, validate_schema

BASIC_AUTH_CP = os.environ['CP201_SP1']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_a_01(connection):
    assert connection.open
    cp = TziChargePoint(BASIC_AUTH_CP, connection)

    start_task = asyncio.create_task(cp.start())
    boot_response = await cp.send_boot_notification()

    assert boot_response is not None
    assert validate_schema(data=boot_response, schema_file_name='BootNotificationResponse.json')
    assert boot_response.status == RegistrationStatusEnumType.accepted

    connectors_status = {
        0: ConnectorStatusEnumType.available,
        1: ConnectorStatusEnumType.occupied,
    }

    for connector_id, status in connectors_status.items():
        status_response = await cp.send_status_notification(connector_id, status)
        assert status_response

    start_task.cancel()
