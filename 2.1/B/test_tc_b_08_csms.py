"""
Test case name      Get Variables - limit to maximum number of values
Test case Id        TC_B_08_CSMS
Use case Id(s)      B06
Requirement(s)      B06.FR.05

Requirement Details:
    B06.FR.05: The CSMS SHALL NOT send more GetVariableData elements in a GetVariablesRequest than reported by
               the Charging Station via ItemsPerMessageGetVariables.
System under test   CSMS

Description         Do not request more variables than supported by MaxItemsPerMessageGetVariables.

Purpose             To test that CSMS does not request more variables than the Charging Station reported to
                    support in the variable MaxItemsPerMessageGetVariables.

Prerequisite(s)     N/a

Configuration State Configure (using getVariablesRequest) Component.Variable.Instance
                    DeviceDataCtrlr.ItemsPerMessage.GetVariables at value 4.

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Manually request CSMS for 5 variables:
    - DeviceDataCtrlr.ItemsPerMessage[ GetReport ]
    - DeviceDataCtrlr.ItemsPerMessage[ GetVariables ]
    - DeviceDataCtrlr.BytesPerMessage[ GetReport ]
    - DeviceDataCtrlr.BytesPerMessage[ GetVariables ]
    - AuthCtrlr.AuthorizeRemoteStart
2. Test System responds with GetVariablesResponse with with a list of 4 GetVariableResultType items and a
   GetVariableResponse with 1 GetVariableResultType item.

Tool validations
* Step 1:
    Message: GetVariablesRequest for 4 variables and a GetVariablesRequest for 1 variable (in arbritrary
             order):
    for component.name = "DeviceDataCtrlr"
    - variable.name = "ItemsPerMessage" with variable.instance = "GetReport"
    - variable.name = "ItemsPerMessage" with variable.instance = "GetVariables"
    - variable.name = "BytesPerMessage" with variable.instance = "GetReport"
    - variable.name = "BytesPerMessage" with variable.instance = "GetVariables"
    and for component.name = "AuthCtrlr"
    - variable.name = "AuthorizeRemoteStart"

Post scenario validations:
    Test System validates that not more than ItemsPerMessageGetVariables elements are requested in one
    GetVariablesRequest message by CSMS.
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from device_model import variable_key
from reusable_states.booted import booted
from trigger import get_variables
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

ITEMS_PER_MESSAGE_GET_VARIABLES = 4

# (component.name, variable.name, variable.instance)
REQUESTED_VARIABLES = [
    ('DeviceDataCtrlr', 'ItemsPerMessage', 'GetReport'),
    ('DeviceDataCtrlr', 'ItemsPerMessage', 'GetVariables'),
    ('DeviceDataCtrlr', 'BytesPerMessage', 'GetReport'),
    ('DeviceDataCtrlr', 'BytesPerMessage', 'GetVariables'),
    ('AuthCtrlr', 'AuthorizeRemoteStart', None),
]


def _get_variable_data(component, variable, instance):
    data = {'component': {'name': component}, 'variable': {'name': variable}}
    if instance is not None:
        data['variable']['instance'] = instance
    return data


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_08(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    cp.variables = {
        'DeviceDataCtrlr.ItemsPerMessage[GetReport]': '4',
        'DeviceDataCtrlr.ItemsPerMessage[GetVariables]': str(ITEMS_PER_MESSAGE_GET_VARIABLES),
        'DeviceDataCtrlr.BytesPerMessage[GetReport]': '65536',
        'DeviceDataCtrlr.BytesPerMessage[GetVariables]': '65536',
        'AuthCtrlr.AuthorizeRemoteStart': 'true',
    }
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Configuration State: Configure (using getVariablesRequest)
    # DeviceDataCtrlr.ItemsPerMessage.GetVariables at value 4. The CSMS reads the value from
    # the Charging Station, which reports 4.
    await cp.wait_for_request(
        'GetVariables',
        manual_action=get_variables(BASIC_AUTH_CP, [
            _get_variable_data('DeviceDataCtrlr', 'ItemsPerMessage', 'GetVariables'),
        ]))

    # 1. Manually request CSMS for 5 variables
    # 2. Test System responds with a GetVariablesResponse with a list of 4
    #    GetVariableResultType items and a GetVariablesResponse with 1 GetVariableResultType
    #    item.
    requests_before = len(cp.requests_of('GetVariables'))
    await cp.wait_for_request(
        'GetVariables',
        manual_action=get_variables(BASIC_AUTH_CP, [
            _get_variable_data(*variable) for variable in REQUESTED_VARIABLES
        ]))
    # The Manual Action is done, so the CSMS has sent all its GetVariablesRequests for it.
    requests = cp.requests_of('GetVariables')[requests_before:]

    # A GetVariablesRequest for 4 variables and a GetVariablesRequest for 1 variable, in
    # arbitrary order, that together ask for the 5 variables
    sizes = sorted(len(request.get_variable_data) for request in requests)
    assert sizes == [1, 4], \
        f"Expected a GetVariablesRequest for 4 variables and one for 1 variable, got sizes {sizes}"
    requested = [variable_key(item) for request in requests for item in request.get_variable_data]
    assert sorted(requested, key=str) == sorted(REQUESTED_VARIABLES, key=str), \
        f"Expected the requests to ask for {REQUESTED_VARIABLES}, got: {requested}"

    # Not more than ItemsPerMessageGetVariables elements are requested in one
    # GetVariablesRequest message by the CSMS.
    for request in requests:
        assert len(request.get_variable_data) <= ITEMS_PER_MESSAGE_GET_VARIABLES, \
            f"GetVariablesRequest with {len(request.get_variable_data)} elements, " \
            f"the Charging Station reported a maximum of {ITEMS_PER_MESSAGE_GET_VARIABLES}"

    start_task.cancel()
