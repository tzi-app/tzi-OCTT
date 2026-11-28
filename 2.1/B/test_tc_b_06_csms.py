"""
Test case name      Get Variables - single value
Test case Id        TC_B_06_CSMS
Use case Id(s)      B06
Requirement(s)      B06.FR.01, B06.FR.02, B06.FR.03, B06.FR.04, B06.FR.10, B06.FR.11

Requirement Details:
    B06.FR.01: The Charging Station SHALL respond with an GetVariablesResponse with an equal (X) number of
               GetVariableResult elements, one for every GetVariableData element in the GetVariablesRequest.
        Precondition: When the Charging Station receives a GetVariablesRequest with an X number of
                      GetVariableData elements
    B06.FR.02: Every GetVariableResult element in the GetVariablesResponse SHALL contain the same component
               and variable combination as one of the GetVariableData elements in the GetVariablesRequest.
        Precondition: B06.FR.01
    B06.FR.03: The corresponding GetVariableResult element in the GetVariablesResponse SHALL also contain the
               same attributeType
        Precondition: B06.FR.02 AND If the GetVariablesRequest contains an attributeType
    B06.FR.04: Every GetVariableResult element in the GetVariablesResponse SHALL contain an attributeValue
               with the value of an attribute from the requested attributeType in the GetVariablesRequest.
        Precondition: B06.FR.01
    B06.FR.10: The Charging Station SHALL set the attributeStatus field in the corresponding GetVariableResult
               to: Accepted and set the attributeValue to the found value.
        Precondition: When the Charging Station was able to get the value requested from a GetVariablesRequest
    B06.FR.11: The corresponding GetVariableResult element in the GetVariablesResponse SHALL contain the
               attributeType Actual.
        Precondition: When the Charging Station receives a GetVariablesRequest without an attributeType.
System under test   CSMS

Description         Get the value of two of the required variables of OCPPCommCtrlr

Purpose             To test getting single value using GetVariablesRequest for one of the
                    mandatory component/variable combinations that must exist in the DM implementation.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Manually request CSMS to get data for:
    - OCPPCommCtrlr.OfflineThreshold
2. Test System responds with: GetVariablesResponse

Tool validations
* Step 1:
    Message: GetVariablesRequest with (in arbitrary order)
    getVariableData[0]:
    - attributeType is at least absent or attributeType = Actual, but Target, MinSet, and MaxSet are also
      allowed
    - variable.name = "OfflineThreshold"
    - component.name = "OCPPCommCtrlr"

Post scenario validations:
    Manually validate that CSMS has correctly read the requested variables.
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from device_model import find_variable
from reusable_states.booted import booted
from trigger import get_variables
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_06(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    cp.variables = {'OCPPCommCtrlr.OfflineThreshold': '60'}
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Manually request CSMS to get data for OCPPCommCtrlr.OfflineThreshold
    # 2. Test System responds with: GetVariablesResponse
    request = await cp.wait_for_request(
        'GetVariables',
        manual_action=get_variables(BASIC_AUTH_CP, [
            {'component': {'name': 'OCPPCommCtrlr'}, 'variable': {'name': 'OfflineThreshold'}},
        ]))

    # getVariableData (in arbitrary order): variable.name "OfflineThreshold",
    # component.name "OCPPCommCtrlr"
    get_variable = find_variable(request.get_variable_data, 'OCPPCommCtrlr', 'OfflineThreshold')
    assert get_variable is not None, \
        f"Expected OCPPCommCtrlr.OfflineThreshold in getVariableData, got: {request.get_variable_data}"
    # attributeType is at least absent or Actual, but Target, MinSet, and MaxSet are also allowed
    assert get_variable.attribute_type in (None, 'Actual', 'Target', 'MinSet', 'MaxSet'), \
        f"Unexpected attributeType: {get_variable.attribute_type}"

    # "Manually validate that CSMS has correctly read the requested variables" is a check on
    # the CSMS itself, which this test cannot do.

    start_task.cancel()
