"""
Test case name      Set new NetworkConnectionProfile - Failed
Test case Id        TC_B_44_CSMS
Use case Id(s)      B09
Requirement(s)      B09.FR.03

Requirement Details:
    B09.FR.03: If setting a valid NetworkConnectionProfile in a SetNetworkProfileRequest fails. The Charging Station SHALL respond by sending a SetNetworkProfileResponse message, with status Failed
        Precondition: If setting a valid NetworkConnectionProfile in a SetNetworkProfileRequest fails.
System under test   CSMS

Description         The CSMS updates the connection details on the Charging Station. For instance in preparation of a
                    migration to a new CSMS.
Purpose             To verify if the CSMS is able to handle a Charging Station responding with status Failed, when
                    setting a new network connection profile at one of the by the Charging Station defined
                    configuration slots.

Prerequisite(s)     N/a

Test Scenario
1. The CSMS sends a SetNetworkProfileRequest
2. The OCTT responds with a SetNetworkProfileResponse with status Failed

Tool validations
    N/a

Post scenario validations:
    - N/a
"""

import asyncio
import pytest
import os
import logging
from ocpp.v201.enums import (
    RegistrationStatusEnumType, ConnectorStatusEnumType,
    SetNetworkProfileStatusEnumType
)

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP_B']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_44(connection):
    """Set new NetworkConnectionProfile - Failed: CS rejects SetNetworkProfileRequest."""
    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    # Configure CP to respond with Failed
    cp._set_network_profile_response_status = SetNetworkProfileStatusEnumType.failed
    start_task = asyncio.create_task(cp.start())

    # Boot to establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Step 1-2: Wait for CSMS to send SetNetworkProfileRequest
    await asyncio.wait_for(
        cp._received_set_network_profile.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._set_network_profile_data is not None
    logging.info(f"SetNetworkProfileRequest received: {cp._set_network_profile_data}")
    logging.info("CS responded with status Failed")

    start_task.cancel()
