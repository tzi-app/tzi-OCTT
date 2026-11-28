"""
Test case name      Update Charging Station Password for HTTP Basic Authentication - Accepted
Test case Id        TC_A_09_CSMS
Use case Id(s)      A01
Requirement(s)      A01.FR.02, A01.FR.03

Requirement Details:
    A01.FR.02: To set a Charging Station’s basic authorization password via OCPP, the CSMS SHALL send the
               Charging Station a SetVariablesRequest message with the BasicAuthPassword Configuration
               Variable.
    A01.FR.03: The CSMS SHALL assume that the authorization key change was successful, and no longer accept
               the credentials previously used by the Charging Station.
        Precondition: A01.FR.02 AND The Charging Station responds to this SetVariablesRequest with a
                      SetVariablesResponse with status Accepted.
System under test   CSMS

Description         This test case defines how to use the BasicAuthPassword, the password used to authenticate
                    Charging Stations in security profile 1 (Basic Authentication) and security profile 2 (TLS
                    with Basic Authentication)

Purpose             To verify if the CSMS is able to successfully set the new BasicAuthPassword and only
                    accepts the new credentials as described at the OCPP specification.

Prerequisite(s)     The CSMS supports security profile 1 and/or 2

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a SetVariablesRequest with:
    setVariableData[1]:
    - variable.name = "BasicAuthPassword"
    - component.name = "SecurityCtrlr"
    - attributeValue = "<NewPassword>"
2. The Test System responds with a SetVariablesResponse with status Accepted
3. The Test System sends a HTTP upgrade request with an Authorization header, containing a username/password
   combination (with the new BasicAuthPassword).
    Note(s):
    - The Authorization header is formatted as follows:
      AUTHORIZATION: Basic <Base64 encoded(<Configured ChargingStationId>:<NEW BasicAuthPassword>)>
4. The CSMS validates the username/password combination AND upgrades the connection to a (secured) WebSocket
   connection.
5. The Test System sends a BootNotificationRequest
6. The CSMS responds with a BootNotificationResponse
7. The Test System notifies the CSMS about the current state of all connectors.
8. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: SetVariableRequest
    - variable.name = "BasicAuthPassword"
    - component.name = "SecurityCtrlr"
* Step 6:
    Message: BootNotificationResponse
    - status must be Accepted

Post scenario validations:
    N/a
"""

import asyncio
import logging
import os

import pytest

from charge_point import TziChargePoint21
from security import connect_with_profile, wait_for_basic_auth_password
from trigger import set_basic_auth_password, trigger_v21

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
async def test_tc_a_09():
    cp_id = BASIC_AUTH_CP

    ws = await connect_with_profile(cp_id, security_profile=1)
    try:
        cp = TziChargePoint21(cp_id, ws)
        start_task = asyncio.create_task(cp.start())

        # 1. The CSMS sends a SetVariablesRequest with variable.name "BasicAuthPassword",
        #    component.name "SecurityCtrlr" and attributeValue "<NewPassword>"
        # 2. The Test System responds with a SetVariablesResponse with status Accepted
        cp.set_variable_status = 'Accepted'
        set_variable = await wait_for_basic_auth_password(
            cp, manual_action=trigger_v21(cp_id, 'update-basic-auth-password'))

        assert set_variable.variable.name == 'BasicAuthPassword'
        assert set_variable.component.name == 'SecurityCtrlr', \
            f"Expected component.name SecurityCtrlr, got: {set_variable.component.name}"

        new_password = set_variable.attribute_value
        assert new_password, "The new password must not be empty"
        logging.info(f"Received new password from CSMS (length={len(new_password)})")

        start_task.cancel()
    finally:
        await ws.close()

    try:
        # 3. The Test System sends a HTTP upgrade request with an Authorization header:
        #    Basic <Base64 encoded(<Configured ChargingStationId>:<NEW BasicAuthPassword>)>
        # 4. The CSMS validates the username/password combination AND upgrades the connection
        #    to a (secured) WebSocket connection.
        ws = await connect_with_profile(cp_id, security_profile=1, password=new_password)
        try:
            cp = TziChargePoint21(cp_id, ws)
            start_task = asyncio.create_task(cp.start())

            # 5. The Test System sends a BootNotificationRequest
            # 6. The CSMS responds with a BootNotificationResponse
            boot_response = await cp.send_boot_notification()
            assert boot_response.status == 'Accepted', \
                f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

            # 7. The Test System notifies the CSMS about the current state of all connectors.
            # 8. The CSMS responds accordingly.
            await cp.send_all_connectors_status('Available')

            start_task.cancel()
        finally:
            await ws.close()
    finally:
        # Restore the configured password, so that other tests are not affected
        await set_basic_auth_password(cp_id, BASIC_AUTH_CP_PASSWORD)
