"""
Test case name      Get Variables - single value
Test case Id        TC_B_06_CSMS
Use case Id(s)      B06
Requirement(s)      B06.FR.01, B06.FR.02, B06.FR.03, B06.FR.04, B06.FR.10, B06.FR.11

Requirement Details:
    B06.FR.01: When the Charging Station receives a GetVariablesRequest with an X number of GetVariableData elements The Charging Station SHALL respond with an GetVariablesResponse with an equal (X) number of GetVariableResult elements, one for every GetVariableData element in the GetVariablesRequest.
        Precondition: When the Charging Station receives a GetVariablesRequest with an X number of GetVariableData elements
    B06.FR.02: AND If the GetVariablesRequest contains an attributeType The corresponding GetVariableResult element in the GetVariablesResponse SHALL also contain the same attributeType B. Provisioning
        Precondition: B06.FR.01
    B06.FR.03: B06.FR.02 AND If the GetVariablesRequest contains an attributeType
        Precondition: B06.FR.02 AND If the GetVariablesRequest contains an attributeType
    B06.FR.04: The CSMS SHALL respond with SetVariablesResponse indicating the result.
        Precondition: B06.FR.01
    B06.FR.10: When the Charging Station was able to get the value requested from a GetVariablesRequest The Charging Station SHALL set the attributeStatus field in the corresponding GetVariableResult to: Accepted and set the attributeValue to the found value.
        Precondition: When the Charging Station was able to get the value requested from a GetVariablesRequest
    B06.FR.11: When the Charging Station receives a GetVariablesRequest without an attributeType. The corresponding GetVariableResult element in the GetVariablesResponse SHALL contain the attributeType Actual.
        Precondition: When the Charging Station receives a GetVariablesRequest without an attributeType.
System under test   CSMS

Description         Get the value of two of the required variables of OCPPCommCtrlr
Purpose             To test getting single value using GetVariablesRequest for one of the
                    mandatory component/variable combinations that must exist in the DM implementation.

Prerequisite(s)     N/a

Test Scenario
1. Manually request CSMS to get data for:
   - OCPPCommCtrlr.OfflineThreshold
2. OCTT responds with GetVariablesResponse

Tool validations
* Step 1:
    Message: GetVariablesRequest with (in arbitrary order)
    getVariableData[0]:
    - attributeType is at least absent or attributeType = Actual, but Target, MinSet, and MaxSet are also allowed
    - variable.name = "OfflineThreshold"
    - component.name = "OCPPCommCtrlr"

Post scenario validations:
    Manually validate that CSMS has correctly read the requested variables.
"""

import asyncio
import pytest
import os
import logging
from ocpp.v201.enums import RegistrationStatusEnumType, ConnectorStatusEnumType

from tzi_charge_point import TziChargePoint
from trigger import get_variables
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_06(connection):
    """Get Variables - single value: CSMS requests OCPPCommCtrlr.OfflineThreshold."""
    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    cp._get_variables_values = {
        'OCPPCommCtrlr.OfflineThreshold': '60',
    }
    start_task = asyncio.create_task(cp.start())

    # Boot to establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Trigger CSMS to send GetVariablesRequest for OCPPCommCtrlr.OfflineThreshold
    trigger_task = asyncio.create_task(get_variables(BASIC_AUTH_CP, [
        {"component": {"name": "OCPPCommCtrlr"}, "variable": {"name": "OfflineThreshold"}},
    ]))

    # Wait for the CS to receive the GetVariablesRequest
    await asyncio.wait_for(
        cp._received_get_variables.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task

    # Validate the GetVariablesRequest content
    assert cp._get_variables_data is not None
    assert len(cp._get_variables_data) >= 1

    get_var = cp._get_variables_data[0]
    variable = get_var.get('variable', {}) if isinstance(get_var, dict) else {}
    component = get_var.get('component', {}) if isinstance(get_var, dict) else {}

    assert variable.get('name') == 'OfflineThreshold', \
        f"Expected OfflineThreshold variable, got: {variable}"
    assert component.get('name') == 'OCPPCommCtrlr', \
        f"Expected OCPPCommCtrlr component, got: {component}"

    # attributeType should be absent or Actual (Target, MinSet, MaxSet also allowed)
    attr_type = get_var.get('attribute_type', get_var.get('attributeType'))
    if attr_type is not None:
        assert attr_type in ('Actual', 'Target', 'MinSet', 'MaxSet'), \
            f"Unexpected attributeType: {attr_type}"

    logging.info("GetVariablesRequest validated successfully")

    start_task.cancel()
