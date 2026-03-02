"""
Test case name      Set Variables - single value
Test case Id        TC_B_09_CSMS
Use case Id(s)      B05
Requirement(s)      B05.FR.01, B05.FR.02, B05.FR.03, B05.FR.10, B05.FR.12

Requirement Details:
    B05.FR.01: When the Charging Station receives a SetVariablesRequest with an X number of SetVariableData elements The Charging Station SHALL respond with an SetVariablesResponse with an equal (X) number of SetVariableResult elements, one for every SetVariableData element in the SetVariablesRequest.
        Precondition: When the Charging Station receives a SetVariablesRequest with an X number of SetVariableData elements
    B05.FR.02: AND If the SetVariablesRequest contains an attributeType The corresponding SetVariableResult element in the SetVariablesResponse SHALL also contain the same attributeType
        Precondition: B05.FR.01
    B05.FR.03: B05.FR.02 AND If the SetVariablesRequest contains an attributeType
        Precondition: B05.FR.02 AND If the SetVariablesRequest contains an attributeType
    B05.FR.10: When the Charging Station was able to set the given value from the SetVariableData The Charging Station SHALL set the attributeStatus field in the corresponding SetVariableResult to: Accepted.
        Precondition: When the Charging Station was able to set the given value from the SetVariableData
    B05.FR.12: When the Charging Station receives a SetVariablesRequest without an attributeType. The corresponding SetVariableResult element in the SetVariablesResponse SHALL contain the attributeType Actual. B. Provisioning 54/491 Part 2 - Specification
        Precondition: When the Charging Station receives a SetVariablesRequest without an attributeType.
System under test   CSMS

Description         Set the value of one of the required variables of OCPPCommCtrlr
Purpose             To test setting a single value using SetVariablesRequest for one of the
                    mandatory component/variable combinations that must exist in the DM implementation.

Prerequisite(s)     N/a

Test Scenario
1. Manually request CSMS to set data for:
   - OCPPCommCtrlr.OfflineThreshold
2. OCTT responds with SetVariablesResponse

Tool validations
* Step 1:
    Message: SetVariablesRequest with (in arbitrary order):
    setVariableData[1]:
    - variable.name = "OfflineThreshold"
    - component.name = "OCPPCommCtrlr"
    - attributeValue = "123"
    - attributeType is absent or attributeType = Actual

Post scenario validations:
    Manually validate that CSMS has correctly set the requested variables.
"""

import asyncio
import pytest
import os
import logging
from ocpp.v201.enums import (
    RegistrationStatusEnumType, ConnectorStatusEnumType, SetVariableStatusEnumType
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
async def test_tc_b_09(connection):
    """Set Variables - single value: CSMS sets OCPPCommCtrlr.OfflineThreshold."""
    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    cp._set_variables_response_status = SetVariableStatusEnumType.accepted
    start_task = asyncio.create_task(cp.start())

    # Boot to establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Wait for CSMS to send SetVariablesRequest
    await asyncio.wait_for(
        cp._received_set_variables.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    # Validate the SetVariablesRequest content
    assert cp._set_variables_data is not None
    assert len(cp._set_variables_data) >= 1

    set_var = cp._set_variables_data[0]
    variable = set_var.get('variable', {}) if isinstance(set_var, dict) else {}
    component = set_var.get('component', {}) if isinstance(set_var, dict) else {}

    assert variable.get('name') == 'OfflineThreshold', \
        f"Expected OfflineThreshold variable, got: {variable}"
    assert component.get('name') == 'OCPPCommCtrlr', \
        f"Expected OCPPCommCtrlr component, got: {component}"

    attr_value = set_var.get('attribute_value', set_var.get('attributeValue'))
    assert attr_value == '123', f'Expected attributeValue "123", got: {attr_value}'
    logging.info(f"SetVariablesRequest: OfflineThreshold = {attr_value}")

    # attributeType should be absent or Actual
    attr_type = set_var.get('attribute_type', set_var.get('attributeType'))
    if attr_type is not None:
        assert attr_type == 'Actual', f"Expected Actual attributeType, got: {attr_type}"

    start_task.cancel()
