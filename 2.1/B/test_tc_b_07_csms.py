"""
Test case name      Get Variables - multiple values
Test case Id        TC_B_07_CSMS
Use case Id(s)      B06
Requirement(s)      B06.FR.01, B06.FR.02, B06.FR.03

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
System under test   CSMS

Description         Get the value of two of the required variables of OCPPCommCtrlr

Purpose             To test getting multiple values using GetVariablesRequest for one of the
                    mandatory component/variable combinations that must exist in the DM implementation.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. CSMS: Manually request CSMS to get data for:
    - OCPPCommCtrlr.OfflineThreshold
    - AuthCtrlr.AuthorizeRemoteStart
2. Charging Station: Test System responds with:
    GetVariablesResponse

Tool validations
* Step 1:
    Message: GetVariablesRequest with (in arbitrary order)
    getVariableData[0]:
    - attributeType is at least absent or attributeType = Actual, but Target, MinSet, and MaxSet are also
      allowed
    - variable.name = "OfflineThreshold"
    - component.name = "OCPPCommCtrlr"
    getVariableData[1]:
    - attributeType is at least absent or attributeType = Actual, but Target, MinSet, and MaxSet are also
      allowed
    - variable.name = "AuthorizeRemoteStart"
    - component.name = "AuthCtrlr"

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

ALLOWED_ATTRIBUTE_TYPES = (None, 'Actual', 'Target', 'MinSet', 'MaxSet')


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_07(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    cp.variables = {
        'OCPPCommCtrlr.OfflineThreshold': '60',
        'AuthCtrlr.AuthorizeRemoteStart': 'true',
    }
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. Manually request CSMS to get data for OCPPCommCtrlr.OfflineThreshold and
    #    AuthCtrlr.AuthorizeRemoteStart
    # 2. Test System responds with: GetVariablesResponse
    request = await cp.wait_for_request(
        'GetVariables',
        manual_action=get_variables(BASIC_AUTH_CP, [
            {'component': {'name': 'OCPPCommCtrlr'}, 'variable': {'name': 'OfflineThreshold'}},
            {'component': {'name': 'AuthCtrlr'}, 'variable': {'name': 'AuthorizeRemoteStart'}},
        ]))

    # One GetVariablesRequest with, in arbitrary order:
    # - variable.name "OfflineThreshold", component.name "OCPPCommCtrlr"
    # - variable.name "AuthorizeRemoteStart", component.name "AuthCtrlr"
    # attributeType is at least absent or Actual, but Target, MinSet, and MaxSet are also allowed
    for component, variable in (('OCPPCommCtrlr', 'OfflineThreshold'),
                                ('AuthCtrlr', 'AuthorizeRemoteStart')):
        get_variable = find_variable(request.get_variable_data, component, variable)
        assert get_variable is not None, \
            f"Expected {component}.{variable} in getVariableData, got: {request.get_variable_data}"
        assert get_variable.attribute_type in ALLOWED_ATTRIBUTE_TYPES, \
            f"Unexpected attributeType for {component}.{variable}: {get_variable.attribute_type}"

    # "Manually validate that CSMS has correctly read the requested variables" is a check on
    # the CSMS itself, which this test cannot do.

    start_task.cancel()
