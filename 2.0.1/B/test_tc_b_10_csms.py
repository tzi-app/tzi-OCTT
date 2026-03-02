"""
Test case name      Set Variables - multiple values
Test case Id        TC_B_10_CSMS
Use case Id(s)      B05
Requirement(s)      B05.FR.01, B05.FR.02, B05.FR.03

Requirement Details:
    B05.FR.01: When the Charging Station receives a SetVariablesRequest with an X number of SetVariableData elements The Charging Station SHALL respond with an SetVariablesResponse with an equal (X) number of SetVariableResult elements, one for every SetVariableData element in the SetVariablesRequest.
        Precondition: When the Charging Station receives a SetVariablesRequest with an X number of SetVariableData elements
    B05.FR.02: AND If the SetVariablesRequest contains an attributeType The corresponding SetVariableResult element in the SetVariablesResponse SHALL also contain the same attributeType
        Precondition: B05.FR.01
    B05.FR.03: B05.FR.02 AND If the SetVariablesRequest contains an attributeType
        Precondition: B05.FR.02 AND If the SetVariablesRequest contains an attributeType
System under test   CSMS

Description         Set the value of two of the required variables of OCPPCommCtrlr
Purpose             To test setting multiple values using SetVariablesRequest for one of the
                    mandatory component/variable combinations that must exist in the DM implementation.

Prerequisite(s)     N/a

Test Scenario
1. Manually request CSMS to set data for:
   - OCPPCommCtrlr.OfflineThreshold
   - AuthCtrlr.AuthorizeRemoteStart
2. OCTT responds with SetVariablesResponse

Tool validations
* Step 1:
    Message: SetVariablesRequest with (in arbitrary order):
    setVariableData[1]:
    - variable.name = "OfflineThreshold"
    - component.name = "OCPPCommCtrlr"
    - attributeValue = "123"
    - attributeType is absent or attributeType = Actual
    setVariableData[2]:
    - variable.name = "AuthorizeRemoteStart"
    - component.name = "AuthCtrlr"
    - attributeValue = "false"
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
async def test_tc_b_10(connection):
    """Set Variables - multiple values: CSMS sets OfflineThreshold and AuthorizeRemoteStart."""
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
    assert len(cp._set_variables_data) >= 2, \
        f"Expected at least 2 variables, got {len(cp._set_variables_data)}"

    # Extract requested variables (order may vary)
    requested_vars = {}
    for item in cp._set_variables_data:
        comp_name = item.get('component', {}).get('name', '')
        var_name = item.get('variable', {}).get('name', '')
        requested_vars[f"{comp_name}.{var_name}"] = item

    assert 'OCPPCommCtrlr.OfflineThreshold' in requested_vars, \
        f"Expected OCPPCommCtrlr.OfflineThreshold, got: {list(requested_vars.keys())}"
    assert 'AuthCtrlr.AuthorizeRemoteStart' in requested_vars, \
        f"Expected AuthCtrlr.AuthorizeRemoteStart, got: {list(requested_vars.keys())}"

    offline_threshold = requested_vars['OCPPCommCtrlr.OfflineThreshold']
    authorize_remote_start = requested_vars['AuthCtrlr.AuthorizeRemoteStart']

    offline_threshold_value = offline_threshold.get('attribute_value', offline_threshold.get('attributeValue'))
    assert offline_threshold_value == '123', \
        f'Expected OfflineThreshold attributeValue "123", got: {offline_threshold_value}'
    offline_threshold_type = offline_threshold.get('attribute_type', offline_threshold.get('attributeType'))
    if offline_threshold_type is not None:
        assert offline_threshold_type == 'Actual', \
            f"Expected OfflineThreshold attributeType Actual, got: {offline_threshold_type}"

    authorize_remote_start_value = authorize_remote_start.get(
        'attribute_value', authorize_remote_start.get('attributeValue')
    )
    assert authorize_remote_start_value == 'false', \
        f'Expected AuthorizeRemoteStart attributeValue "false", got: {authorize_remote_start_value}'
    authorize_remote_start_type = authorize_remote_start.get(
        'attribute_type', authorize_remote_start.get('attributeType')
    )
    if authorize_remote_start_type is not None:
        assert authorize_remote_start_type == 'Actual', \
            f"Expected AuthorizeRemoteStart attributeType Actual, got: {authorize_remote_start_type}"

    logging.info("SetVariablesRequest with multiple values validated successfully")

    start_task.cancel()
