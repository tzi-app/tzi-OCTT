"""
Test case name      Update Charging Station Password for HTTP Basic Authentication - Accepted
Test case Id        TC_A_09_CSMS
Use case Id(s)      A01
Requirement(s)      A01.FR.02, A01.FR.03

Requirement Details:
    A01.FR.02: To set a Charging Station's basic authorization password via OCPP, the CSMS SHALL send the Charging Station a SetVariablesRequest message with the BasicAuthPassword Configuration Variable. A. Security 30/491 Part 2 - Specification
    A01.FR.03: A01.FR.02 AND The Charging Station responds to this SetVariablesRequest with a SetVariablesResponse with status Accepted.
        Precondition: A01.FR.02 AND The Charging Station responds to this SetVariablesRequest with a SetVariablesResponse with status Accepted.
System under test   CSMS

Description         This test case defines how to use the BasicAuthPassword, the password used to authenticate Charging
                    Stations in security profile 1 (Basic Authentication) and security profile 2 (TLS with Basic
                    Authentication)

Purpose             To verify if the CSMS is able to successfully set the new BasicAuthPassword and only accepts the new
                    credentials as described at the OCPP specification.

Prerequisite(s)     The CSMS supports security profile 1 and/or 2

Test Scenario
1. The CSMS sends a SetVariablesRequest with:
    setVariableData[1]:
    - variable.name = "BasicAuthPassword"
    - component.name = "SecurityCtrlr"
    - attributeValue = "<NewPassword>"
2. The OCTT responds with a SetVariablesResponse with status Accepted
3. The OCTT sends a HTTP upgrade request with an Authorization header, containing a
   username/password combination (with the new BasicAuthPassword).

    Note(s):
    - The Authorization header is formatted as follows:
      AUTHORIZATION: Basic <Base64 encoded(<Configured ChargingStationId>:<NEW BasicAuthPassword>)>

4. The CSMS validates the username/password combination AND upgrades the connection to a
   (secured) WebSocket connection.
5. The OCTT sends a BootNotificationRequest
6. The CSMS responds with a BootNotificationResponse
7. The OCTT notifies the CSMS about the current state of all connectors.
8. The CSMS responds accordingly.

    Note(s):
    - Steps 5, 6, 7, and 8 are only required when status in Step 2 is RebootRequired

Tool validations
* Step 1:
    Message: SetVariablesRequest
    - variable.name = "BasicAuthPassword"
    - component.name = "SecurityCtrlr"

* Step 6:
    Message: BootNotificationResponse
    - status must be Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os
import time
import logging

import pytest
import websockets

from ocpp.v201.enums import (
    RegistrationStatusEnumType, ConnectorStatusEnumType, SetVariableStatusEnumType
)

from tzi_charge_point import TziChargePoint
from trigger import trigger_v201, set_basic_auth_password
from utils import get_basic_auth_headers, create_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
TLS_CA_CERT = os.environ['TLS_CA_CERT']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_a_09():
    cp_id = BASIC_AUTH_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'

    # Connect with current password
    ssl_ctx = create_ssl_context(ca_cert=TLS_CA_CERT)
    headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )

    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    cp._set_variables_response_status = SetVariableStatusEnumType.accepted
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Trigger the CSMS to send SetVariablesRequest with BasicAuthPassword
    trigger_task = asyncio.create_task(
        trigger_v201(cp_id, 'update-basic-auth-password')
    )

    # Wait for CSMS to send SetVariablesRequest with BasicAuthPassword
    # (CSMS may send other SetVariablesRequests first, e.g. TariffFallbackMessage)
    deadline = asyncio.get_event_loop().time() + CSMS_ACTION_TIMEOUT
    set_var = None
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        assert remaining > 0, "Timed out waiting for SetVariablesRequest with BasicAuthPassword"
        cp._received_set_variables.clear()
        await asyncio.wait_for(
            cp._received_set_variables.wait(),
            timeout=remaining,
        )
        assert cp._set_variables_data is not None
        for var in cp._set_variables_data:
            if var.get('variable', {}).get('name') == 'BasicAuthPassword':
                set_var = var
                break
        if set_var is not None:
            break
        logging.info(f"Ignoring non-BasicAuthPassword SetVariablesRequest: {cp._set_variables_data}")

    assert set_var.get('component', {}).get('name') == 'SecurityCtrlr', \
        f"Expected SecurityCtrlr component, got: {set_var}"

    new_password = set_var.get('attribute_value', set_var.get('attributeValue'))
    assert new_password, "New password must not be empty"
    logging.info(f"Received new password from CSMS (length={len(new_password)})")

    # Wait for the CSMS to receive the CALLRESULT and persist the new password
    await asyncio.wait_for(trigger_task, timeout=CSMS_ACTION_TIMEOUT)

    start_task.cancel()
    await ws.close()

    # Step 3-4: Reconnect with the NEW password
    new_headers = get_basic_auth_headers(cp_id, new_password)
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=new_headers,
        ssl=ssl_ctx,
    )

    time.sleep(0.5)

    # Step 5-8: Boot + Status + NotifyEvent
    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)
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

    # Restore original password so other tests are not affected
    await set_basic_auth_password(cp_id, BASIC_AUTH_CP_PASSWORD)
